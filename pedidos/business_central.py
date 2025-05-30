
import os
import requests
from requests_ntlm import HttpNtlmAuth
import logging

logger = logging.getLogger(__name__)

class BusinessCentralClient:
    def __init__(self):
        self.base_url = os.getenv("BC_API_BASE_URL")
        self.items_url = os.getenv("BC_API_ITEMS_URL")
        self.company_id = os.getenv("BC_COMPANY_ID")
        self.auth = HttpNtlmAuth(
            f"{os.getenv('BC_DOMAIN')}\\{os.getenv('BC_USERNAME')}",
            os.getenv("BC_PASSWORD")
        )
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def get_item_info(self, item_id):
        url = f"{self.base_url}/companies({self.company_id})/items({item_id})"
        resp = requests.get(url, auth=self.auth, headers=self.headers)
        if resp.status_code != 200:
            raise Exception(f"Error consultando item: {resp.status_code} - {resp.text}")
        return resp.json()

    def get_item_info_complete(self, item_id):
        url = f"{self.items_url}/companies({self.company_id})/items({item_id})"
        resp = requests.get(url, auth=self.auth, headers=self.headers)
        if resp.status_code != 200:
            raise Exception(f"Error consultando item: {resp.status_code} - {resp.text}")
        return resp.json()

    def get_location_ids(self):
        url = f"{self.base_url}/locations"
        resp = requests.get(url, auth=self.auth, headers=self.headers)
        if resp.status_code != 200:
            raise Exception(f"Error obteniendo almacenes: {resp.status_code} - {resp.text}")
        return {
            loc["displayName"].strip().upper(): loc["id"]
            for loc in resp.json().get("value", [])
            if loc.get("displayName") and loc.get("id")
        }

    def delete_purchase_order(self, order_id):
        url = f"{self.base_url}/companies({self.company_id})/purchaseOrders({order_id})"
        resp = requests.delete(url, auth=self.auth, headers=self.headers)
        if resp.status_code != 204:
            raise Exception(f"No se pudo eliminar el pedido: {resp.status_code} - {resp.text}")

    def create_purchase_order(self, proveedor_codigo):
        url = f"{self.base_url}/companies({self.company_id})/purchaseOrders"
        data = {
            "vendorNumber": proveedor_codigo
        }
        resp = requests.post(url, auth=self.auth, headers=self.headers, json=data)

        if resp.status_code == 201:
            response_data = resp.json()
            return {
                "id": response_data["id"],  # ← Usar este para añadir líneas
                "number": response_data["number"]  # ← Usar este para mostrar o guardar
            }

        raise Exception(f"Error al crear pedido: {resp.status_code} - {resp.text}")

    def add_purchase_order_line(self, order_id, item_id, cantidad, location_id=None):
        item_info = self.get_item_info(item_id)
        nombre = item_info.get("displayName","unknown")
        precio = item_info.get("unitCost", 0)
        if not precio or precio == 0:
            raise Exception(f"Artículo '{nombre}' tiene precio 0 y no se puede añadir a la orden.")

        descripcion = item_info.get("displayName") or item_info.get("description") or ""

        url = f"{self.base_url}/companies({self.company_id})/purchaseOrders({order_id})/purchaseOrderLines"
        data = {
            "itemId": item_id,
            "quantity": float(cantidad),
            "directUnitCost": float(precio),
            "description": descripcion
        }

        if location_id:
            data["locationId"] = location_id

        resp = requests.post(url, auth=self.auth, headers=self.headers, json=data)
        if resp.status_code != 201:
            raise Exception(f"Error al añadir línea: {resp.status_code} - {resp.text}")

    def create_sales_order(self, data):
        url = f"{self.base_url}/companies({self.company_id})/salesOrders"
        resp = requests.post(url, auth=self.auth, headers=self.headers, json=data)
        if resp.status_code != 201:
            raise Exception(f"Error al crear pedido de venta: {resp.status_code} - {resp.text}")
        return resp.json()
	
    def delete_sales_order(self, order_id):
        url = f"{self.base_url}/companies({self.company_id})/salesOrders({order_id})"
        resp = requests.delete(url, auth=self.auth, headers=self.headers)
        if resp.status_code != 204:
            raise Exception(f"No se pudo eliminar el pedido de venta: {resp.status_code} - {resp.text}")

    def add_sales_order_line(self, sales_order_id, item_id, cantidad, descripcion="",
                             location_id=None):
        url = f"{self.base_url}/companies({self.company_id})/salesOrders({sales_order_id})/salesOrderLines"
        data = {
            "itemId": item_id,
            "quantity": float(cantidad),
            "description": descripcion
        }
        if location_id:
            data["locationId"] = location_id
        resp = requests.post(url, auth=self.auth, headers=self.headers, json=data)
        if resp.status_code != 201:
            raise Exception(f"Error al añadir línea de venta: {resp.status_code} - {resp.text}")

