import os
from typing import List, Dict, Any
from langchain_core.documents import Document

class ProductCatalog:
    def __init__(self):
        # Lazy imports to avoid crashing if dependencies are missing in strict envs
        from langchain_openai import OpenAIEmbeddings
        from langchain_postgres.vectorstores import PGVector
        
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Connection String (Adjust protocol for psycopg)
        # Default: postgresql+psycopg://user:pass@localhost:5432/sales_db
        db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/sales_db")
        if "postgresql://" in db_url and "psycopg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

        self.vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name="product_catalog",
            connection=db_url,
            use_jsonb=True,
        )

    def add_products(self, products: List[Dict[str, Any]]):
        """
        Ingest products into the vector store.
        Expects dicts with 'id', 'name', 'description', 'price', etc.
        """
        documents = []
        for p in products:
            # Create a rich description for semantic search
            page_content = f"Product: {p.get('name')}\nDescription: {p.get('description')}\nFeatures: {p.get('features', '')}"
            
            # Store structured data in metadata for filtering
            metadata = {
                "sku": p.get("id"), # Using ID as SKU
                "price": float(p.get("price", 0)),
                "stock": int(p.get("stock", 0)),
                "image_url": p.get("image_url", ""),
                "category": p.get("category", "general")
            }
            documents.append(Document(page_content=page_content, metadata=metadata))
        
        if documents:
            self.vector_store.add_documents(documents)
            print(f"Indexados {len(documents)} productos en Postgres (pgvector).")

    def search_semantic(self, query: str, k: int = 3) -> List[Dict]:
        """
        Find products matching the user's description (e.g., 'zapatos para correr').
        """
        docs = self.vector_store.similarity_search(query, k=k)
        results = []
        for doc in docs:
            item = doc.metadata.copy()
            item["description_snippet"] = doc.page_content
            results.append(item)
        return results

    def get_product_by_sku(self, sku: str) -> Dict:
        """
        Retrieve exact product details (simulating a DB lookup via metadata filter).
        """
        # Hack: Use similarity search with exact filter to find the item
        # We search for the SKU itself as text to hint the vector engine, plus strict filter.
        docs = self.vector_store.similarity_search(sku, k=1, filter={"sku": sku})
        if docs:
            return docs[0].metadata
        return None
