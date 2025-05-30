import os
from django.core.management.base import BaseCommand
from previsiones.models import ArticuloPrevision
from requests_ntlm import HttpNtlmAuth
import requests
from dotenv import load_dotenv

load_dotenv()

class Command(BaseCommand):
    help = "Sincroniza todos los artículos con los datos más actuales desde Business Central"

    def handle(self, *args, **options):
        self.stdout.write("🔍 Obteniendo todos los artículos existentes...")

        articulos = ArticuloPrevision.objects.filter(anio=2024)
        self.stdout.write(f"📦 Total artículos en base: {articulos.count()}")

        BASE_URL = os.getenv("BC_API_BASE_URL")
        BASE_URL_ITEMS = os.getenv("BC_API_ITEMS_URL")
        USERNAME = os.getenv("BC_USERNAME")
        PASSWORD = os.getenv("BC_PASSWORD")
        DOMAIN = os.getenv("BC_DOMAIN")
        COMPANY_NAME = os.getenv("BC_COMPANY_NAME")

        if not all([BASE_URL, BASE_URL_ITEMS, USERNAME, PASSWORD, DOMAIN, COMPANY_NAME]):
            self.stderr.write("❌ Faltan variables de entorno necesarias.")
            return

        self.stdout.write("🌐 Consultando todos los items desde Business Central...")

        auth = HttpNtlmAuth(f"{DOMAIN}\\{USERNAME}", PASSWORD)
        headers = {"Accept": "application/json", "User-Agent": "PythonApp"}

        # Obtener ID de empresa desde BASE_URL
        resp = requests.get(f"{BASE_URL}/companies", auth=auth, headers=headers)
        if resp.status_code != 200:
            self.stderr.write(f"❌ Error al obtener la empresa: {resp.status_code}")
            return
        data = resp.json().get("value", [])
        company_id = next((c["id"] for c in data if c["name"].strip().lower() == COMPANY_NAME.strip().lower()), None)
        if not company_id:
            self.stderr.write("❌ Empresa no encontrada en BC.")
            return

        # Obtener item categories (familias)
        self.stdout.write("📂 Cargando nombres de familias desde itemCategories...")
        familias = {}
        resp = requests.get(f"{BASE_URL}/companies({company_id})/itemCategories", auth=auth, headers=headers)
        if resp.status_code == 200:
            familias = {
                item.get("code", "").strip(): item.get("displayName", "—")
                for item in resp.json().get("value", [])
                if item.get("code")
            }
        else:
            self.stderr.write("❌ Error al cargar itemCategories")
            return

        # Obtener items con campos explícitos
        all_items = []
        skip = 0
        while True:
            url = (
                f"{BASE_URL_ITEMS}/companies({company_id})/items"
                f"?$skip={skip}&$select=id,No,Description,ItemCategoryCode,VendorNo"
            )
            resp = requests.get(url, auth=auth, headers=headers)
            if resp.status_code != 200:
                self.stderr.write(f"❌ Error al obtener los items: {resp.status_code} - {resp.text}")
                return
            batch = resp.json().get("value", [])
            if not batch:
                break
            all_items.extend(batch)
            skip += len(batch)

        items_map = {item.get("No").lstrip("0"): item for item in all_items if item.get("No")}
        self.stdout.write(f"📦 Total items en BC: {len(items_map)}")

        total_actualizados = 0
        total_no_encontrados = 0

        for art in articulos:
            ident = str(art.identificacion).strip().lstrip("0")
            item = items_map.get(ident)

            if not item:
                self.stdout.write(f"[❌ NO ENCONTRADO] Artículo ID {art.id} → identificacion '{ident}'")
                total_no_encontrados += 1
                continue

            codigo_familia = (item.get("ItemCategoryCode") or "").strip()
            nombre_familia = familias.get(codigo_familia, art.familia)

            if not nombre_familia or nombre_familia == "—":
                self.stdout.write(
                    f"[⚠️ FAMILIA NO ENCONTRADA] Código '{codigo_familia}' no resuelto para artículo '{art.codigo}' (ident: {art.identificacion})"
                )

            # Actualización: guardamos el código viejo, y asignamos el nuevo ID
            art.codigo = art.identificacion
            art.identificacion = item.get("id")
            art.descripcion = item.get("Description", art.descripcion)
            art.proveedor = item.get("VendorNo") or art.proveedor
            art.familia = nombre_familia
            art.save()

            self.stdout.write(f"[✔️ ACTUALIZADO] ID {art.id} → identificador='{art.identificacion}', proveedor='{art.proveedor}', familia='{art.familia}'")
            total_actualizados += 1

        self.stdout.write("\n✅ Sincronización completa.")
        self.stdout.write(f"   Total actualizados: {total_actualizados}")
        self.stdout.write(f"   Total no encontrados: {total_no_encontrados}")
