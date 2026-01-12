import streamlit as st
import pandas as pd
from app.database.vector_store import ProductCatalog
import os

# Configuración de Página
st.set_page_config(page_title="🛍️ Panel de Agente de Ventas", layout="wide")

# Inicializar Catálogo
@st.cache_resource
def get_catalog():
    return ProductCatalog()

catalog = get_catalog()

st.title("🛍️ Gestor de Productos - Agente de Ventas")

# Pestañas
tab1, tab2, tab3 = st.tabs(["➕ Agregar Producto", "🔍 Buscar e Inspeccionar", "📊 Estadísticas"])

with tab1:
    st.header("Agregar Nuevo Producto")
    with st.form("add_product_form"):
        col1, col2 = st.columns(2)
        with col1:
            sku = st.text_input("SKU / ID", placeholder="ej., ZAP-001")
            name = st.text_input("Nombre del Producto", placeholder="ej., Zapatillas Running Pro")
            price = st.number_input("Precio", min_value=0.0, step=0.01)
        with col2:
            category = st.selectbox("Categoría", ["calzado", "ropa", "electronica", "accesorios", "otro"])
            stock = st.number_input("Cantidad en Stock", min_value=0, step=1)
            image_url = st.text_input("URL de Imagen (Opcional)")

        description = st.text_area("Descripción", placeholder="Descripción detallada para la búsqueda semántica...")
        features = st.text_area("Características (Separadas por comas)", placeholder="Transpirable, Ligero, Impermeable")

        submitted = st.form_submit_button("💾 Guardar Producto")
        
        if submitted:
            if not sku or not name:
                st.error("¡El SKU y el Nombre son obligatorios!")
            else:
                product_data = {
                    "id": sku,
                    "name": name,
                    "description": description,
                    "features": features,
                    "price": price,
                    "stock": stock,
                    "category": category,
                    "image_url": image_url
                }
                
                with st.spinner("Indexando producto..."):
                    try:
                        catalog.add_products([product_data])
                        st.success(f"✅ ¡Producto {name} ({sku}) agregado exitosamente!")
                    except Exception as e:
                        st.error(f"Error al agregar producto: {e}")

with tab2:
    st.header("Buscar en el Catálogo")
    query = st.text_input("Consulta Semántica", placeholder="ej., 'zapatos para senderismo'")
    
    if query:
        results = catalog.search_semantic(query, k=5)
        if results:
            for item in results:
                with st.expander(f"{item.get('name')} (SKU: {item.get('sku')})"):
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        if item.get("image_url"):
                            st.image(item.get("image_url"), width=150)
                        else:
                            st.info("Sin Imagen")
                    with c2:
                        st.markdown(f"**Descripción:** {item.get('description_snippet')}")
                        st.markdown(f"**Precio:** ${item.get('price')} | **Stock:** {item.get('stock')}")
                        st.json(item) # Mostrar metadatos crudos
        else:
            st.warning("No se encontraron coincidencias.")

with tab3:
    st.header("Estadísticas de la Base de Datos")
    st.info("Estadísticas detalladas no disponibles en modo PGVector por el momento.")
