# sustituciones/views.py
import json

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST

from .models import SustitucionArticulo
from django.utils.timezone import now
from previsiones.models import ArticuloPrevision
from sustituciones.models import SustitucionArticulo
from decimal import Decimal
from pedidos.business_central import BusinessCentralClient
@staff_member_required
def sustituir_articulo(request):
    sustituciones = SustitucionArticulo.objects.order_by("-fecha_aplicacion")
    return render(request, "sustituciones/sustituciones.html", {"sustituciones": sustituciones})

@staff_member_required
def verificar_articulo_db(request, identificador):
    articulo = ArticuloPrevision.objects.filter(identificacion=identificador).first()
    if not articulo:
        return JsonResponse({"error": "No encontrado"}, status=404)

    return JsonResponse({
        "identificacion": articulo.identificacion,
        "codigo": articulo.codigo,
        "descripcion": articulo.descripcion,
        "familia": articulo.familia,
        "proveedor": articulo.proveedor or None
    })


@staff_member_required
def verificar_articulo_bc(request, codigo):
    cliente = BusinessCentralClient()
    try:
        info = cliente.get_item_info_complete(codigo)  # usa versión extendida

        return JsonResponse({
            "id": info.get("id"),
            "No": info.get("No"),
            "Description": info.get("Description"),
            "GenProdPostingGroup": info.get("GenProdPostingGroup"),
            "VendorNo": info.get("VendorNo")
        })
    except Exception:
        return JsonResponse({"error": "No encontrado en BC"}, status=404)

@staff_member_required
@require_POST
def aplicar_sustitucion(request):
    data = json.loads(request.body)

    identificador_viejo = data.get("identificador_viejo")
    identificador_nuevo = data.get("identificador_nuevo")
    operacion = data.get("operacion")  # 'multiplicar' o 'dividir'
    factor = Decimal(data.get("factor"))

    if not identificador_viejo or not identificador_nuevo or not factor:
        return JsonResponse({"success": False, "error": "Datos incompletos"}, status=400)

    client = BusinessCentralClient()
    try:
        nuevo_articulo = client.get_item_info_complete(identificador_nuevo)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

    nuevo_codigo = nuevo_articulo.get("No")
    nueva_descripcion = nuevo_articulo.get("Description")
    nuevo_proveedor = nuevo_articulo.get("VendorNo", "")
    nueva_familia = nuevo_articulo.get("GenProdPostingGroup", "")

    registros = ArticuloPrevision.objects.filter(identificacion=identificador_viejo)
    total_afectados = registros.count()

    for art in registros:
        # Convertir a Decimal para evitar errores de tipo
        prevision = Decimal(str(art.prevision_venta))

        # Aplicar factor si no es 1
        if factor != 1:
            if operacion == "multiplicar":
                prevision *= factor
            elif operacion == "dividir" and factor != 0:
                prevision /= factor

            # Recalcular stock solo si ha habido modificación
            if art.familia == "COCKTAILS":
                art.stock_seguridad = prevision * Decimal("0.5")
            else:
                art.stock_seguridad = prevision * Decimal("0.33")

            art.cantidad_stock_final = prevision + art.stock_seguridad
            art.prevision_venta = prevision

        # Actualizar datos comunes
        art.identificacion = identificador_nuevo
        art.codigo = nuevo_codigo
        art.descripcion = nueva_descripcion
        art.proveedor = nuevo_proveedor
        art.familia = nueva_familia
        art.save()

    SustitucionArticulo.objects.create(
        identificador_original=identificador_viejo,
        nuevo_identificador=identificador_nuevo,
        operacion=operacion,
        factor=factor,
        fecha=now(),
        nombre=nueva_descripcion
    )

    return JsonResponse({
        "success": True,
        "mensaje": f"{total_afectados} registros actualizados correctamente."
    })
