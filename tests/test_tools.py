import pytest
from unittest.mock import MagicMock, patch
from app.tools.product_tools import check_inventory, get_product_media, lookup_product_info
from app.tools.search_tools import web_search_product

# --- Test Info Tools (MOVED TO SYSTEM PROMPT) ---
# Logic moved to system prompt as per user request.

# --- Test Product Tools (Mocked Catalog) ---

@patch("app.tools.product_tools.get_catalog")
def test_check_inventory_logic(mock_get_catalog):
    # Setup mock
    mock_catalog = mock_get_catalog.return_value
    
    # Case 1: Item in stock + accessories (Pickup available)
    mock_catalog.get_product_by_sku.return_value = {
        "stock": 10,
        "category": "accessories",
        "name": "Gorra"
    }
    result = check_inventory.invoke("SKU_123")
    assert "10 unidades" in result
    assert "Recogida en Tienda" in result

    # Case 2: Item in stock + bulky (No pickup)
    mock_catalog.get_product_by_sku.return_value = {
        "stock": 5,
        "category": "furniture",
        "name": "Silla"
    }
    result = check_inventory.invoke("SKU_456")
    assert "5 unidades" in result
    assert "Envío a Domicilio" in result
    assert "Recogida en Tienda" not in result

    # Case 3: Out of stock
    mock_catalog.get_product_by_sku.return_value = {"stock": 0, "name": "Bicicleta"}
    result = check_inventory.invoke("SKU_000")
    assert "0 unidades" in result or "Stock actual: 0" in result

@patch("app.tools.product_tools.get_catalog")
def test_get_product_media(mock_get_catalog):
    mock_catalog = mock_get_catalog.return_value
    # Case 1: Media exists
    mock_catalog.get_product_by_sku.return_value = {
        "image_url": "http://img.com/shoe.jpg"
    }
    result = get_product_media.invoke("SKU_IMG")
    assert result["url"] == "http://img.com/shoe.jpg"
    assert result["media_type"] == "image"

    # Case 2: No media
    mock_catalog.get_product_by_sku.return_value = {}
    result = get_product_media.invoke("SKU_NO_IMG")
    assert "error" in result

# --- Test Web Search (Mocked Tavily) ---

@patch("app.tools.search_tools.TavilySearchResults")
def test_web_search_tool(mock_tavily_class):
    # Setup mock instance
    mock_instance = mock_tavily_class.return_value
    mock_instance.invoke.return_value = [
        {"url": "http://review.com", "content": "Great product!"},
        {"url": "http://specs.com", "content": "Size 10 dim."}
    ]
    
    result = web_search_product.invoke("reviews for nike shoes")
    
    assert "Resultados de la web" in result
    assert "http://review.com" in result
    assert "Great product!" in result
