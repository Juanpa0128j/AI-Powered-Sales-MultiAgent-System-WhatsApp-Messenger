from typing import Optional
from langchain_core.tools import tool
from app.database.vector_store import ProductCatalog
from functools import lru_cache

# Lazy Singleton to prevent init at import time (fixes testing in CI/restricted envs)
@lru_cache(maxsize=1)
def get_catalog():
    return ProductCatalog()

@tool
def lookup_product_info(query: str):
    """
    Useful to find products based on a description or feature. 
    E.g., 'shoes for running' or 'something simple'.
    Returns a list of matching products with their details.
    """
    results = get_catalog().search_semantic(query)
    if not results:
        return "No encontré productos con esa descripción."
    return str(results)

@tool
def check_inventory(sku: str):
    """
    Check stock for a specific SKU. 
    Returns stock quantity and if it's available for pickup.
    """
    product = get_catalog().get_product_by_sku(sku)
    if not product:
        return f"Error: SKU {sku} no encontrado."
    
    stock = product.get("stock", 0)
    msg = f"Stock actual: {stock} unidades."
    if stock > 0:
        # Business Logic: Only some items might be pickup-able (mock logic here)
        msg += " Disponible para Envío a Domicilio."
        if product.get("category") == "accessories": # Example condition
            msg += " También disponible para Recogida en Tienda."
    return msg

@tool
def get_product_media(sku: str):
    """
    Get the image/video URL for a product SKU.
    """
    product = get_catalog().get_product_by_sku(sku)
    if not product or not product.get("image_url"):
        return {"error": "Media no disponible"}
    
    # Return structured dict for the Agent to pass to the Gateway
    return {
        "media_type": "image",
        "url": product.get("image_url")
    }
