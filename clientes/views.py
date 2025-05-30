import json

from django.contrib.admin.views.decorators import staff_member_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.shortcuts import render
from datetime import datetime
from previsiones.models import ArticuloPrevision
from .utils import obtener_clientes, buscar_pedidos_por_cliente, obtener_lineas_pedido
from pedidos.business_central import BusinessCentralClient
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from clientes.scripts import enviar_nuevo_pedido_venta

@staff_member_required
def buscar_clientes(request):
    try:
        clientes = obtener_clientes()
        return render(request, "clientes/buscar_clientes.html", {"clientes": clientes})
    except Exception as e:
        return render(request, "clientes/error_bc.html", {
            "error_message": "No se pudo establecer conexión con Business Central. Intente de nuevo más tarde.",
            "detalles": str(e)
        })


@staff_member_required
def ver_pedidos_cliente(request, cliente_id):
    pedidos = buscar_pedidos_por_cliente(cliente_id)
    campos = ["id", "number", "orderDate", "totalAmountIncludingTax"]

    datos = [
        {k: pedido.get(k) for k in campos}
        for pedido in pedidos
        if float(pedido.get("totalAmountIncludingTax", 0)) > 0
    ]

    return JsonResponse({"pedidos": datos})

@staff_member_required
def api_buscar_clientes(request):
    termino = request.GET.get("term", "").lower()
    coincidencias = []

    for cliente in obtener_clientes():
        nombre = cliente.get("displayName", "").lower()
        numero = cliente.get("number", "").lower()

        if termino and termino not in nombre and termino not in numero:
            continue

        coincidencias.append({
            "id": cliente["id"],
            "text": f"{cliente['displayName']} ({cliente['number']})"
        })

    return JsonResponse({"results": coincidencias})


@staff_member_required
def ver_pedido_detalle(request, pedido_id):
    bc = BusinessCentralClient()
    lineas, pedido_info = obtener_lineas_pedido(pedido_id)

    location_name_to_id = bc.get_location_ids()
    location_id_to_name = {v: k for k, v in location_name_to_id.items()}

    articulos = []
    familias_set = set()
    codigos_set = set()

    for linea in lineas:
        if linea.get("lineType") != "Item":
            continue

        item_id = linea.get("itemId") or linea.get("lineId") or ""

        # Buscar artículo localmente por identificacion (UUID)
        articulo_local = ArticuloPrevision.objects.filter(identificacion=item_id).first()
        codigo = articulo_local.codigo if articulo_local else "—"
        familia = articulo_local.familia if articulo_local else "—"

        try:
            info = bc.get_item_info_complete(item_id)
            precio_unitario = info.get("UnitCost", 0)
        except Exception:
            precio_unitario = 0

        articulo = {
            "codigo": codigo,
            "identificacion": item_id,
            "descripcion": linea.get("description", ""),
            "familia": familia,
            "almacen": location_id_to_name.get(linea.get("locationId"), "Desconocido"),
            "fecha": pedido_info.get("orderDate", "—")[:7],
            "precio_unitario": precio_unitario,
            "cantidad_stock_final": linea.get("quantity", 0),
            "stock_seguridad": 0,
            "prevision_venta": 0,
        }

        familias_set.add(familia)
        codigos_set.add(codigo)
        articulos.append(articulo)

    pedido_location_id = pedido_info.get("locationId")
    pedido_location_nombre = location_id_to_name.get(
        pedido_location_id,
        pedido_info.get("locationCode", "—")
    )

    if pedido_location_nombre == "—" and articulos:
        almacenes_usados = {a["almacen"] for a in articulos if a["almacen"] != "Desconocido"}
        if len(almacenes_usados) == 1:
            pedido_location_nombre = almacenes_usados.pop()

    # Todos los artículos disponibles en base de datos para alimentar los selects
    todos_los_articulos = ArticuloPrevision.objects.values(
        "codigo", "descripcion", "familia", "identificacion", "almacen"
    ).distinct()

    context = {
        "pedido": {
            "id": pedido_id,
            "almacen": pedido_location_nombre
        },
        "articulos": articulos,
        "articulos_db": todos_los_articulos,
        "selected_familias": list(familias_set),
        "selected_codigos": list(codigos_set),
        "selected_fecha": pedido_info.get("orderDate", "—")[:7],
        "todos_los_articulos_json": json.dumps(list(todos_los_articulos), cls=DjangoJSONEncoder),
        "familias": sorted({a["familia"] for a in todos_los_articulos if a.get("familia")}),
    }

    context.update({
        "customerId": pedido_info.get("customerId"),
        "sellToName": pedido_info.get("sellToName"),
        "sellToAddressLine1": pedido_info.get("sellToAddressLine1"),
        "sellToCity": pedido_info.get("sellToCity"),
        "sellToPostCode": pedido_info.get("sellToPostCode"),
    })

    return render(request, "clientes/recuperar_pedido_bc.html", context)


@csrf_exempt
@staff_member_required
def crear_pedido_venta_bc(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        payload = json.loads(request.body)
        resultado = enviar_nuevo_pedido_venta(payload)

        # Devolvemos directamente el objeto plano (no lo envolvemos)
        return JsonResponse(resultado)

    except Exception as e:
        return JsonResponse({
            "resultado": "error",
            "mensaje": f"Error general del servidor: {str(e)}"
        }, status=500)


@staff_member_required
def crear_pedido_desde_cero(request):
    cliente_id = request.GET.get("cliente")
    if not cliente_id:
        return render(request, "clientes/crear_pedido.html", {
            "mensaje": "No se ha proporcionado ningún cliente para crear el pedido."
        })

    # === Recuperar filtros desde GET ===
    selected_familia = request.GET.getlist("familia")
    selected_articulo = request.GET.getlist("articulo")
    selected_fecha = datetime.now().strftime("%Y-%m")
    selected_almacen = request.GET.get("almacen", "")

    # Paso 1: filtrar artículos ignorando completamente el almacén
    filtros = Q()
    if selected_familia:
        filtros &= Q(familia__in=selected_familia)
    if selected_articulo:
        codigos = [a.split("|||")[0] for a in selected_articulo]
        filtros &= Q(codigo__in=codigos)

    articulos_qs = ArticuloPrevision.objects.filter(filtros).values(
        "codigo", "descripcion", "familia", "identificacion"
    ).order_by("codigo")

    # Eliminar duplicados manualmente por código
    vistos = set()
    articulos_db = []
    for art in articulos_qs:
        if art["codigo"] in vistos:
            continue
        vistos.add(art["codigo"])
        articulos_db.append({
            "codigo": art["codigo"],
            "descripcion": art.get("descripcion", ""),
            "familia": art.get("familia", ""),
            "identificacion": art.get("identificacion", ""),
            "almacen": selected_almacen
        })

    # === Cliente ===
    clientes = obtener_clientes()
    cliente = next((c for c in clientes if c.get("id") == cliente_id), {})

    context = {
        "customerId": cliente_id,
        "sellToName": cliente.get("displayName", ""),
        "sellToAddressLine1": cliente.get("address", {}).get("street", ""),
        "sellToCity": cliente.get("address", {}).get("city", ""),
        "sellToPostCode": cliente.get("address", {}).get("postalCode", ""),
        "familias": sorted({a["familia"] for a in articulos_db if a.get("familia")}),
        "articulos": articulos_db,
        "todos_los_articulos_json": json.dumps(articulos_db, cls=DjangoJSONEncoder),
        "selected_familia": selected_familia,
        "selected_articulo": selected_articulo,
        "selected_fecha": selected_fecha,
        "selected_almacen": selected_almacen,
    }

    return render(request, "clientes/crear_pedido.html", context)


