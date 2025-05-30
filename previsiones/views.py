
from django.shortcuts import render
from previsiones.models import ArticuloPrevision
from django.db.models import Q
from django.views.decorators.http import require_GET
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
import io
from math import ceil
@staff_member_required
def buscar_previsiones(request):
    familias = ArticuloPrevision.objects.values_list('familia', flat=True).distinct().order_by('familia')
    resultados = []
    articulos = []

    selected_articulo = request.GET.getlist('articulo')
    selected_familia = request.GET.getlist('familia')
    selected_fecha = request.GET.get('fecha', '')
    selected_almacen = request.GET.get('almacen', '')

    if request.GET:
        fecha = selected_fecha
        familias_seleccionadas = selected_familia
        articulos_seleccionados = selected_articulo
        almacen = selected_almacen

        filtros_articulos = Q()
        if familias_seleccionadas:
            filtros_articulos &= Q(familia__in=familias_seleccionadas)

        articulos_qs = ArticuloPrevision.objects.filter(
            filtros_articulos, almacen=almacen
        ).values("codigo", "descripcion", "familia", "identificacion").distinct()

        if fecha:
            anio, mes = fecha.split('-')
            anio = int(anio) - 1
            mes = int(mes)
        else:
            anio = mes = None

        codigos_solicitados = [a.split("|||")[0] if "|||" in a else a for a in articulos_seleccionados]
        codigos_actuales = set()

        for art in articulos_qs:
            codigo = art["codigo"]
            if codigos_solicitados and codigo not in codigos_solicitados:
                continue
            codigos_actuales.add(codigo)

            prevision = ArticuloPrevision.objects.filter(
                codigo=codigo,
                familia=art["familia"],
                almacen=almacen,
                anio=anio,
                mes=mes
            ).first() if anio and mes else None

            if prevision:
                resultados.append({
                    "codigo": prevision.codigo,
                    "identificacion": prevision.identificacion,
                    "descripcion": prevision.descripcion,
                    "familia": prevision.familia,
                    "almacen": prevision.almacen,
                    "cantidad_stock_final": prevision.cantidad_stock_final,
                    "prevision_venta": round(prevision.prevision_venta),
                    "stock_seguridad": ceil(prevision.stock_seguridad),
                    "fecha": f"{prevision.mes:02d}/{prevision.anio}",
                })
            else:
                resultados.append({
                    "codigo": codigo,
                    "identificacion": art.get("identificacion", ""),
                    "descripcion": art.get("descripcion", ""),
                    "familia": art.get("familia", ""),
                    "almacen": almacen,
                    "cantidad_stock_final": 0,
                    "prevision_venta": 0,
                    "stock_seguridad": 0,
                    "fecha": f"{mes:02d}/{anio}" if anio and mes else "-",
                })

        # Extra: completar con artículos de otros almacenes que no están en `articulos_qs`
        articulos_posibles = ArticuloPrevision.objects.filter(
            filtros_articulos
        ).exclude(codigo__in=codigos_actuales).values(
            "codigo", "descripcion", "familia", "identificacion"
        )

        vistos = set()
        articulos_extra = []
        for art in articulos_posibles:
            clave = (art["codigo"], art["familia"])
            if clave not in vistos:
                vistos.add(clave)
                articulos_extra.append(art)

        for art in articulos_extra:
            if codigos_solicitados and art["codigo"] not in codigos_solicitados:
                continue

            resultados.append({
                "codigo": art["codigo"],
                "identificacion": art.get("identificacion", ""),
                "descripcion": art.get("descripcion", ""),
                "familia": art.get("familia", ""),
                "almacen": almacen,
                "cantidad_stock_final": 0,
                "prevision_venta": 0,
                "stock_seguridad": 0,
                "fecha": f"{mes:02d}/{anio}" if anio and mes else "-",
            })

        articulos = articulos_qs

    articulos_json = json.dumps([
        {
            "codigo": a["codigo"],
            "descripcion": a.get("descripcion", ""),
            "familia": a.get("familia", "")
        }
        for a in articulos
    ], cls=DjangoJSONEncoder)

    return render(request, 'previsiones/buscar_previsiones.html', {
        'familias': familias,
        'resultados': resultados,
        'articulos': articulos,
        'selected_familia': selected_familia,
        'selected_articulo': selected_articulo,
        'selected_fecha': selected_fecha,
        'selected_almacen': selected_almacen,
        'todos_los_articulos_json': articulos_json,
    })



def api_previsiones_por_articulo(request):
    almacen = request.GET.get("almacen")
    articulos_seleccionados = request.GET.getlist("articulos[]")
    fecha = request.GET.get("fecha")  # opcional: MM/YYYY

    if not almacen or not articulos_seleccionados:
        return JsonResponse({"articulos": []})

    anio = mes = None
    if fecha:
        try:
            mes, anio = map(int, fecha.split("/"))
        except ValueError:
            return JsonResponse({"error": "Formato de fecha inválido"}, status=400)

    articulos_resultado = []

    for codigo in articulos_seleccionados:
        qs = ArticuloPrevision.objects.filter(codigo=codigo, almacen=almacen)
        if anio and mes:
            qs = qs.filter(anio=anio, mes=mes)

        articulo = qs.first()

        if articulo:
            articulos_resultado.append({
                "codigo": articulo.codigo,
                "identificacion": articulo.identificacion,
                "descripcion": articulo.descripcion,
                "proveedor": articulo.proveedor,
                "familia": articulo.familia,
                "prevision_venta": float(articulo.prevision_venta),
                "stock_seguridad": float(articulo.stock_seguridad),
                "cantidad_stock_final": float(articulo.cantidad_stock_final),
                "almacen": articulo.almacen,
            })
        else:
            articulos_resultado.append({
                "codigo": codigo,
                "identificacion": "",
                "descripcion": "(Sin previsión)",
                "proveedor": "",
                "familia": "",
                "prevision_venta": 0,
                "stock_seguridad": 0,
                "cantidad_stock_final": 0,
                "almacen": almacen,
            })

    return JsonResponse({"articulos": articulos_resultado})



@require_GET
@staff_member_required
def api_articulos_por_familia(request):
    familias_param = request.GET.get("familias", "")
    if not familias_param:
        return JsonResponse({"articulos": []})

    familias = familias_param.split(",")
    if not any(familias):
        return JsonResponse({"articulos": []})

    articulos_qs = ArticuloPrevision.objects.filter(
        familia__in=familias
    ).values("codigo", "descripcion", "identificacion" ,"familia")

    # Eliminar duplicados exactos por (codigo + descripcion)
    vistos = set()
    articulos_filtrados = []
    for a in articulos_qs:
        clave = (a["codigo"], a["descripcion"])
        if clave not in vistos:
            vistos.add(clave)
            articulos_filtrados.append(a)

    return JsonResponse({"articulos": articulos_filtrados})

@require_POST
@staff_member_required
def ejecutar_importar_bc(request):
    buffer = io.StringIO()
    call_command('importar_bc', stdout=buffer)
    salida = buffer.getvalue()

    # Extraer el número de registros desde la última línea
    total = 0
    for line in salida.splitlines():
        if "registros guardados" in line:
            total = int(''.join(filter(str.isdigit, line)))
            break

    return JsonResponse({"ok": True, "total": total})