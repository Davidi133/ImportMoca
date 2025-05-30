import os
import time
import requests
from requests_ntlm import HttpNtlmAuth

# Cachés simples en memoria
cache_clientes = {"data": None, "timestamp": 0}
cache_pedidos = {}  # clave = cliente_id, valor = {"data": ..., "timestamp": ...}
TTL = 300  # Tiempo en segundos (5 minutos)

def obtener_clientes():
    ahora = time.time()
    if cache_clientes["data"] is not None and (ahora - cache_clientes["timestamp"] < TTL):
        return cache_clientes["data"]

    BASE_URL = os.getenv("BC_API_BASE_URL")
    USERNAME = os.getenv("BC_USERNAME")
    PASSWORD = os.getenv("BC_PASSWORD")
    DOMAIN = os.getenv("BC_DOMAIN")

    auth = HttpNtlmAuth(f"{DOMAIN}\\{USERNAME}", PASSWORD)
    headers = {"Accept": "application/json", "User-Agent": "PythonApp"}

    url_clientes = f"{BASE_URL}/customers"
    response = requests.get(url_clientes, auth=auth, headers=headers)
    response.raise_for_status()
    clientes = response.json().get("value", [])

    # Guardar en caché
    cache_clientes["data"] = clientes
    cache_clientes["timestamp"] = ahora

    return clientes

def buscar_pedidos_por_cliente(cliente_id):
    ahora = time.time()
    if cliente_id in cache_pedidos:
        if ahora - cache_pedidos[cliente_id]["timestamp"] < TTL:
            return cache_pedidos[cliente_id]["data"]

    BASE_URL = os.getenv("BC_API_BASE_URL")
    USERNAME = os.getenv("BC_USERNAME")
    PASSWORD = os.getenv("BC_PASSWORD")
    DOMAIN = os.getenv("BC_DOMAIN")
    COMPANY_NAME = os.getenv("BC_COMPANY_NAME")

    auth = HttpNtlmAuth(f"{DOMAIN}\\{USERNAME}", PASSWORD)
    headers = {"Accept": "application/json", "User-Agent": "PythonApp"}

    # Obtener ID empresa
    resp = requests.get(f"{BASE_URL}/companies", auth=auth, headers=headers)
    resp.raise_for_status()
    company_id = next(
        (c["id"] for c in resp.json().get("value", []) if c["name"].strip().lower() == COMPANY_NAME.strip().lower()),
        None
    )
    if not company_id:
        raise Exception(f"No se encontró la empresa con nombre: {COMPANY_NAME}")

    url_pedidos = f"{BASE_URL}/companies({company_id})/salesOrders"
    response = requests.get(
        url_pedidos,
        auth=auth,
        headers=headers,
        params={"$filter": f"customerId eq {cliente_id}"}
    )

    response.raise_for_status()
    pedidos = response.json().get("value", [])

    # Ordenar por fecha descendente
    pedidos.sort(key=lambda x: x.get("orderDate", ""), reverse=True)

    # Guardar en caché
    cache_pedidos[cliente_id] = {
        "data": pedidos,
        "timestamp": ahora
    }

    return pedidos

def obtener_lineas_pedido(pedido_id):
    BASE_URL = os.getenv("BC_API_BASE_URL")
    USERNAME = os.getenv("BC_USERNAME")
    PASSWORD = os.getenv("BC_PASSWORD")
    DOMAIN = os.getenv("BC_DOMAIN")
    COMPANY_NAME = os.getenv("BC_COMPANY_NAME")

    auth = HttpNtlmAuth(f"{DOMAIN}\\{USERNAME}", PASSWORD)
    headers = {"Accept": "application/json", "User-Agent": "PythonApp"}

    # Obtener company_id
    resp = requests.get(f"{BASE_URL}/companies", auth=auth, headers=headers)
    resp.raise_for_status()
    company_id = next(
        (c["id"] for c in resp.json().get("value", []) if c["name"].strip().lower() == COMPANY_NAME.strip().lower()),
        None
    )
    if not company_id:
        raise Exception(f"No se encontró la empresa con nombre: {COMPANY_NAME}")

    # Obtener pedido
    pedido_url = f"{BASE_URL}/companies({company_id})/salesOrders({pedido_id})"
    pedido_resp = requests.get(pedido_url, auth=auth, headers=headers)
    pedido_resp.raise_for_status()
    pedido_info = pedido_resp.json()

    # Obtener líneas
    lineas_url = f"{pedido_url}/salesOrderLines"
    lineas_resp = requests.get(lineas_url, auth=auth, headers=headers)
    lineas_resp.raise_for_status()
    lineas = lineas_resp.json().get("value", [])

    # Resolver nombres de almacenes
    loc_resp = requests.get(f"{BASE_URL}/companies({company_id})/locations", auth=auth, headers=headers)
    loc_map = {
        loc["id"]: loc["displayName"]
        for loc in loc_resp.json().get("value", [])
        if loc.get("id") and loc.get("displayName")
    }

    for l in lineas:
        l["locationNombre"] = loc_map.get(l.get("locationId"), "Desconocido")

    return lineas, pedido_info
