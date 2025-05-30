from django.contrib.admin.views.decorators import staff_member_required
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from pedidos.models import Pedido, LineaPedido, ResumenPedidoBusinessCentral
from pedidos.scripts import generar_ordenes_compra_desde_pedidos
from previsiones.models import ArticuloPrevision
from django.http import JsonResponse
from math import ceil

@staff_member_required
def crear_pedido(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            almacen = data.get('almacen')
            fecha_prevision = data.get('fecha_prevision')
            familias = data.get('familias')
            articulos = data.get('articulos', [])

            if not almacen or not fecha_prevision or not familias or not articulos:
                return JsonResponse({'error': 'Faltan datos'}, status=400)

            pedido = Pedido.objects.create(
                almacen=almacen,
                fecha_prevision=fecha_prevision,
                familias=familias,
                creado_por=request.user
            )

            anio = int(fecha_prevision[:4]) - 1
            mes = int(fecha_prevision[5:7])

            for art in articulos:
                codigo = art.get('codigo')
                cantidad_solicitada = art.get('cantidad')

                if not codigo:
                    continue
                try:
                    cantidad_solicitada = float(cantidad_solicitada)
                except (TypeError, ValueError):
                    continue

                # Buscar previsión exacta primero
                try:
                    articulo = ArticuloPrevision.objects.get(
                        codigo=codigo,
                        anio=anio,
                        mes=mes,
                        almacen=almacen
                    )
                    identificador = articulo.identificacion
                except ArticuloPrevision.DoesNotExist:
                    # Buscar cualquier previsión anterior
                    articulo_fallback = (
                        ArticuloPrevision.objects
                        .filter(codigo=codigo)
                        .order_by("-anio", "-mes")
                        .first()
                    )
                    identificador = articulo_fallback.identificacion if articulo_fallback else ""

                LineaPedido.objects.create(
                    pedido=pedido,
                    codigo_producto=codigo,
                    identificador=identificador,
                    cantidad=cantidad_solicitada,
                    cantidad_stock_final=cantidad_solicitada
                )

            return JsonResponse({'success': True, 'pedido_id': pedido.id})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Error en el formato del JSON'}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@staff_member_required
def lista_pedidos(request):
    pedidos = Pedido.objects.all().order_by("-fecha_creacion")
    resúmenes_bc = ResumenPedidoBusinessCentral.objects.select_related("pedido").order_by("-fecha_creado")

    return render(request, "pedidos/lista_pedidos.html", {
        "pedidos": pedidos,
        "resúmenes_bc": resúmenes_bc
    })

@staff_member_required
def recuperar_pedido(request, pedido_id):
    from django.core.serializers.json import DjangoJSONEncoder

    pedido = get_object_or_404(Pedido, id=pedido_id, creado_por=request.user)
    lineas = LineaPedido.objects.filter(pedido=pedido)

    articulos = []
    familias_set = set()
    codigos_set = set()

    # Año anterior para buscar previsiones
    anio, mes = pedido.fecha_prevision.split("-")
    anio = int(anio) - 1
    mes = int(mes)

    selected_fecha = f"{anio + 1}-{str(mes).zfill(2)}"

    # Lista completa de artículos para posibles datos de fallback
    todos_los_articulos = ArticuloPrevision.objects.values(
        "codigo", "descripcion", "familia", "identificacion", "almacen"
    ).distinct()

    for linea in lineas:
        try:
            articulo = ArticuloPrevision.objects.get(
                codigo=linea.codigo_producto,
                anio=anio,
                mes=mes,
                almacen=pedido.almacen
            )
            articulos.append({
                "codigo": articulo.codigo,
                "identificacion": articulo.identificacion,
                "descripcion": articulo.descripcion,
                "familia": articulo.familia,
                "almacen": articulo.almacen,
                "fecha": f"{str(articulo.mes).zfill(2)}/{articulo.anio}",
                "stock_seguridad": ceil(articulo.stock_seguridad),
                "prevision_venta": articulo.prevision_venta,
                "cantidad_stock_final": linea.cantidad
            })
            familias_set.add(articulo.familia)
            codigos_set.add(articulo.codigo)

        except ArticuloPrevision.DoesNotExist:
            # Buscar descripción/familia en todos_los_articulos por código + identificador
            datos = next(
                (a for a in todos_los_articulos
                 if a["codigo"] == linea.codigo_producto and a["identificacion"] == linea.identificador),
                {}
            )
            articulos.append({
                "codigo": linea.codigo_producto,
                "identificacion": linea.identificador,
                "descripcion": datos.get("descripcion", ""),
                "familia": datos.get("familia", ""),
                "almacen": pedido.almacen,
                "fecha": f"{str(mes).zfill(2)}/{anio}",
                "stock_seguridad": 0,
                "prevision_venta": 0,
                "cantidad_stock_final": linea.cantidad
            })
            if datos.get("familia"):
                familias_set.add(datos["familia"])
            codigos_set.add(linea.codigo_producto)

    articulos_db = ArticuloPrevision.objects.order_by("codigo", "-anio", "-mes")

    context = {
        "pedido": pedido,
        "articulos": articulos,
        "familias": sorted(set(a.familia for a in articulos_db)),
        "articulos_db": todos_los_articulos,
        "selected_familias": list(familias_set),
        "selected_codigos": list(codigos_set),
        "selected_fecha": selected_fecha,
        "todos_los_articulos_json": json.dumps(list(todos_los_articulos), cls=DjangoJSONEncoder),
    }

    return render(request, "pedidos/recuperar_pedido.html", context)

@csrf_exempt
@staff_member_required()
def confirmar_pedidos_bc(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        pedidos_ids = [int(i) for i in data.get("pedidos", [])]

        resultados = generar_ordenes_compra_desde_pedidos(pedidos_ids)

        for pedido in Pedido.objects.filter(id__in=pedidos_ids):
            pedido.estado = "procesado"
            if not pedido.fecha_procesado:
                pedido.fecha_procesado = timezone.now()
            pedido.save()

        return JsonResponse({"resultados": resultados})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
