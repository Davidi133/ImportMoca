import json
from collections import defaultdict
from pedidos.models import LineaPedido, Pedido, ResumenPedidoBusinessCentral
from previsiones.models import ArticuloPrevision
from pedidos.business_central import BusinessCentralClient

def generar_ordenes_compra_desde_pedidos(pedidos_ids):
    cliente_bc = BusinessCentralClient()
    location_map = cliente_bc.get_location_ids()

    resumen_pedidos = defaultdict(lambda: {"ids_bc": [], "proveedores": []})
    resultados = []

    for pedido_id in pedidos_ids:
        pedido = Pedido.objects.get(id=pedido_id)
        lineas = LineaPedido.objects.filter(pedido=pedido)

        grupos = defaultdict(list)
        proveedor_cache = {}

        for linea in lineas:
            articulo = ArticuloPrevision.objects.filter(codigo=linea.codigo_producto).order_by("-id").first()
            proveedor = None

            if articulo:
                proveedor = articulo.proveedor

            if not proveedor and articulo and articulo.identificacion:
                try:
                    info_bc = cliente_bc.get_item_info_complete(articulo.identificacion)
                    proveedor = info_bc.get("VendorNo")
                except Exception as e:
                    resultados.append({
                        "pedido_id": pedido_id,
                        "resultado": "error",
                        "mensaje": f"Error obteniendo proveedor desde BC para {articulo.codigo}: {str(e)}"
                    })

            if not proveedor:
                nombre_articulo = articulo.descripcion or articulo.codigo
                resultados.append({
                    "pedido_id": pedido.id,
                    "resultado": "error",
                    "mensaje": f"<span style='color:red;'>Pedido {pedido.id}: Artículo <strong>{nombre_articulo}</strong> sin proveedor</span>"
                })
                continue

            proveedor_cache[linea.identificador] = (proveedor, articulo)

            grupos[proveedor].append((
                linea.identificador,
                linea.cantidad,
                linea.codigo_producto,
                pedido.almacen.strip().upper(),
                pedido.id
            ))

        for proveedor, lineas in grupos.items():
            if not lineas:
                continue
            try:
                respuesta = cliente_bc.create_purchase_order(proveedor)
                order_id = respuesta["id"]
                order_number = respuesta["number"]
            except Exception as e:
                resultados.append({
                    "pedido_id": pedido_id,
                    "resultado": "error",
                    "mensaje": f"Error creando pedido para proveedor {proveedor}: {str(e)}"
                })
                continue

            lineas_validas = []
            for item_id, cantidad, codigo, almacen_nombre, pid in lineas:
                location_id = location_map.get(almacen_nombre)
                if not location_id:
                    resultados.append({
                        "pedido_id": pid,
                        "resultado": "error",
                        "mensaje": f"<span> Pedido {pid}: Almacén <strong>{almacen_nombre}</strong> no encontrado en BC</span>"
                    })
                    continue

                try:
                    cliente_bc.add_purchase_order_line(order_id, item_id, cantidad, location_id)
                    lineas_validas.append(item_id)
                except Exception as e:
                    articulo = ArticuloPrevision.objects.filter(identificacion=item_id).first()
                    nombre = articulo.descripcion if articulo else codigo
                    resultados.append({
                        "pedido_id": pid,
                        "resultado": "error",
                        "mensaje": f"<span> Pedido {pid}: Artículo <strong>{nombre}</strong> sin precio o no se pudo añadir</span>"
                    })

            if not lineas_validas:
                try:
                    cliente_bc.delete_purchase_order(order_id)
                    resultados.append({
                        "pedido_id": pedido.id,
                        "resultado": "error",
                        "mensaje": f"<span> Pedido {pedido.id}: No se añadió ninguna línea. El pedido fue eliminado automáticamente.</span>"
                    })
                except Exception as e:
                    resultados.append({
                        "pedido_id": pedido.id,
                        "resultado": "error",
                        "mensaje": f"<span> Pedido {pedido.id}: Fallo al eliminar pedido vacío: {str(e)}</span>"
                    })
                continue

            resumen_pedidos[pedido.id]["ids_bc"].append(order_number)
            resumen_pedidos[pedido.id]["proveedores"].append(proveedor)

            resultados.append({
                "pedido_id": pedido_id,
                "resultado": "ok",
                "numero": order_number,
            })

    for pid, datos in resumen_pedidos.items():
        pedido = Pedido.objects.get(id=pid)
        resumen, _ = ResumenPedidoBusinessCentral.objects.get_or_create(pedido=pedido)

        ids_existentes = json.loads(resumen.pedidos_bc_ids) if resumen.pedidos_bc_ids else []
        proveedores_existentes = json.loads(resumen.proveedores) if resumen.proveedores else []

        resumen.pedidos_bc_ids = json.dumps(list(set(ids_existentes + datos["ids_bc"])))
        resumen.proveedores = json.dumps(list(set(proveedores_existentes + datos["proveedores"])))
        resumen.save()

    return resultados
