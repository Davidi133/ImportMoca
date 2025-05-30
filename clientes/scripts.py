from django.utils import timezone
from pedidos.business_central import BusinessCentralClient

def enviar_nuevo_pedido_venta(payload):
    cliente_bc = BusinessCentralClient()
    location_map = cliente_bc.get_location_ids()

    customer_id = payload.get("customerId")
    almacen = payload.get("almacen", "").strip().upper()
    location_id = location_map.get(almacen)
    hoy = timezone.now().date().isoformat()

    if not customer_id or not location_id:
        return {
            "resultado": "error",
            "mensajes": [f"Datos inválidos: customerId={customer_id}, almacen={almacen}"]
        }

    cabecera = {
        "customerId": customer_id,
        "orderDate": hoy,
        "postingDate": hoy,
        "currencyCode": "EUR",
        "pricesIncludeTax": False,
        "paymentTermsId": payload.get("paymentTermsId", "de6543ef-6aca-ee11-9d01-005056a6b8c3"),
    }

    try:
        respuesta = cliente_bc.create_sales_order(cabecera)
        sales_order_id = respuesta["id"]
        sales_order_number = respuesta["number"]
    except Exception as e:
        return {
            "resultado": "error",
            "mensajes": [f"Error creando pedido de venta: {str(e)}"]
        }

    articulos = payload.get("articulos", [])
    hubo_linea_exitosa = False
    mensajes_error = []

    for art in articulos:
        item_id = art.get("itemId")
        cantidad = art.get("cantidad")
        descripcion = art.get("descripcion", "")

        if not item_id or not cantidad:
            mensajes_error.append(f"Artículo sin ID o cantidad inválida: {descripcion}")
            continue

        try:
            cliente_bc.add_sales_order_line(
                sales_order_id=sales_order_id,
                item_id=item_id,
                cantidad=cantidad,
                descripcion=descripcion,
                location_id=location_id
            )
            hubo_linea_exitosa = True
        except Exception as e:
            mensajes_error.append(f"Error añadiendo artículo <strong>{descripcion}</strong>")

    if not hubo_linea_exitosa:
        try:
            cliente_bc.delete_sales_order(sales_order_id)
        except Exception:
            pass
        return {
            "resultado": "error",
            "mensajes": mensajes_error,
            "pedido_borrado": True
        }

    if mensajes_error:
        return {
            "resultado": "ok",
            "numero": sales_order_number,
            "mensajes": mensajes_error
        }

    return {
        "resultado": "ok",
        "numero": sales_order_number
    }
