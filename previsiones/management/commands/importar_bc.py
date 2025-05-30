import os
import requests
from requests_ntlm import HttpNtlmAuth
from collections import defaultdict
from dotenv import load_dotenv
from datetime import datetime
from django.core.management.base import BaseCommand
from previsiones.models import ArticuloPrevision
from django.db.models import Sum

load_dotenv()

def articulos_clave(codigo, nombre):
    return f"{codigo}-{nombre.replace(' ', '')[:10]}"

class Command(BaseCommand):
    help = "Importa previsiones desde Business Central"

    def handle(self, *args, **options):
        BASE_URL = os.getenv("BC_API_BASE_URL")
        BASE_URL_ITEMS = os.getenv("BC_API_ITEMS_URL")
        USERNAME = os.getenv("BC_USERNAME")
        PASSWORD = os.getenv("BC_PASSWORD")
        DOMAIN = os.getenv("BC_DOMAIN")
        COMPANY_NAME = os.getenv("BC_COMPANY_NAME")

        auth = HttpNtlmAuth(f"{DOMAIN}\\{USERNAME}", PASSWORD)
        headers = {"Accept": "application/json", "User-Agent": "PythonApp"}

        self.stdout.write("🔑 Obteniendo ID de empresa...")
        resp = requests.get(f"{BASE_URL}/companies", auth=auth, headers=headers)
        resp.raise_for_status()
        company_id = next(
            (c["id"] for c in resp.json().get("value", []) if c["name"].strip().lower() == COMPANY_NAME.strip().lower()),
            None
        )
        if not company_id:
            raise Exception(f"No se encontró la empresa con nombre: {COMPANY_NAME}")
        self.stdout.write(f"✅ Empresa encontrada: {company_id}")

        def cargar_familias():
            url = f"{BASE_URL}/companies({company_id})/itemCategories"
            r = requests.get(url, auth=auth, headers=headers)
            if r.status_code == 200:
                return {
                    fam.get("code"): fam.get("displayName", "—")
                    for fam in r.json().get("value", [])
                    if fam.get("code")
                }
            return {}

        self.stdout.write("📦 Recolectando pedidos de venta...")
        pedidos = []
        skip = 0
        while True:
            paged = f"{BASE_URL}/companies({company_id})/salesOrders?$skip={skip}"
            resp = requests.get(paged, auth=auth, headers=headers)
            data = resp.json().get("value", [])
            if not data:
                break
            pedidos.extend(data)
            skip += len(data)

        self.stdout.write("📊 Analizando líneas...")
        ventas_por_articulo = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

        location_cache = {}
        resp = requests.get(f"{BASE_URL}/companies({company_id})/locations", auth=auth, headers=headers)
        for loc in resp.json().get("value", []):
            location_cache[loc["id"]] = loc["code"]

        for pedido in pedidos:
            pedido_id = pedido["id"]
            lines_url = f"{BASE_URL}/companies({company_id})/salesOrders({pedido_id})/salesOrderLines"
            resp = requests.get(lines_url, auth=auth, headers=headers)
            if resp.status_code != 200:
                continue
            for linea in resp.json().get("value", []):
                item_id = linea.get("itemId")
                if not item_id:
                    continue
                fecha_str = linea.get("shipmentDate") or linea.get("postingDate")
                if not fecha_str:
                    continue
                fecha = datetime.fromisoformat(fecha_str.split("T")[0])
                mes = f"{fecha.year}-{fecha.month:02d}"
                cantidad = float(linea.get("quantity", 0))
                almacen_id = linea.get("locationId", "")
                almacen = location_cache.get(almacen_id, "Desconocido")
                ventas_por_articulo[item_id][mes][almacen] += cantidad

        self.stdout.write("📦 Cargando artículos...")
        familias = cargar_familias()
        info_articulos = {}
        skip = 0
        while True:
            url = f"{BASE_URL_ITEMS}/companies({company_id})/items?$skip={skip}"
            resp = requests.get(url, auth=auth, headers=headers)
            data = resp.json().get("value", [])
            if not data:
                break
            for item in data:
                item_id = item.get("id")
                cod_familia = item.get("ItemCategoryCode", "—")
                info_articulos[item_id] = {
                    "codigo": item.get("No", "").strip(),
                    "nombre": item.get("Description", "").strip(),
                    "familia_cod": cod_familia,
                    "familia_nom": familias.get(cod_familia, "—"),
                    "proveedor": item.get("VendorNo", "—"),
                }
            skip += len(data)

        self.stdout.write("💾 Guardando previsiones agrupadas...")
        total = 0
        duplicados = 0
        for item_id, meses in ventas_por_articulo.items():
            info = info_articulos.get(item_id)
            if not info or not info["codigo"]:
                continue
            identificador = item_id

            for mes, almacenes in meses.items():
                anio, mes_int = map(int, mes.split("-"))
                for almacen, cantidad in almacenes.items():
                    stock_seg = round(cantidad * 0.5) if info["familia_cod"] == "1-1" else round(cantidad * 0.33)
                    total_final = round(cantidad + stock_seg)

                    obj, created = ArticuloPrevision.objects.update_or_create(
                        codigo=info["codigo"],
                        anio=anio,
                        mes=mes_int,
                        almacen=almacen,
                        identificacion=identificador,
                        defaults={
                            'descripcion': info["nombre"],
                            'familia': info["familia_nom"],
                            'proveedor': info["proveedor"],
                            'cantidad_compra': 0,
                            'prevision_venta': cantidad,
                            'stock_seguridad': stock_seg,
                            'cantidad_stock_final': total_final,
                        }
                    )

                    if not created:
                        duplicados += 1
                        pre_venta_antigua = obj.prevision_venta
                        obj.prevision_venta += cantidad
                        obj.stock_seguridad = round(obj.prevision_venta * 0.5) if info["familia_cod"] == "1-1" else round(obj.prevision_venta * 0.33)
                        obj.cantidad_stock_final = round(obj.prevision_venta + obj.stock_seguridad)
                        obj.save()
                        self.stdout.write(
                            f"🔁 Fusionado duplicado: código={obj.codigo}, identificador={obj.identificacion}, año={anio}, mes={mes_int}, almacen={almacen}\n"
                            f"   - Previsión original: {pre_venta_antigua} → nueva: {obj.prevision_venta}"
                        )
                    total += 1

        self.stdout.write(f"\n✅ Importación completada: {total} registros guardados o actualizados.")
        self.stdout.write(f"🔁 Duplicados fusionados: {duplicados}")

        # NUEVO BLOQUE: Insertar registros base con cantidad 0 para artículos sin ventas
        self.stdout.write("➕ Insertando artículos sin ventas para visibilidad...")

        almacenes_extra = ["MALLORCA", "MENORCA", "IBIZA"]
        anio_extra = 2023
        mes_extra = 11
        registros_extra = 0

        for item_id, info in info_articulos.items():
            if item_id in ventas_por_articulo:
                continue  # Ya procesado

            for almacen in almacenes_extra:
                ArticuloPrevision.objects.get_or_create(
                    codigo=info["codigo"],
                    anio=anio_extra,
                    mes=mes_extra,
                    almacen=almacen,
                    identificacion=item_id,
                    defaults={
                        'descripcion': info["nombre"],
                        'familia': info["familia_nom"],
                        'proveedor': info["proveedor"],
                        'cantidad_compra': 0,
                        'prevision_venta': 0,
                        'stock_seguridad': 0,
                        'cantidad_stock_final': 0,
                    }
                )
                registros_extra += 1

        self.stdout.write(f"🆗 Insertados {registros_extra} registros base para artículos sin ventas.")
