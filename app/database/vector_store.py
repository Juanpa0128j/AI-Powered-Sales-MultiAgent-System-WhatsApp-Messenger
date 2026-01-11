import os
from typing import List, Dict, Any
from langchain_core.documents import Document

class ProductCatalog:
    def __init__(self):
        # Lazy imports to avoid crashing if dependencies (like ctypes/libffi) are missing in strict envs
        # or during restricted testing.
        from langchain_openai import OpenAIEmbeddings
        from langchain_chroma import Chroma
        
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        # Persistent local vector store
        self.vector_store = Chroma(
            collection_name="product_catalog",
            embedding_function=self.embeddings,
            persist_directory="./chroma_db"
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
            print(f"Indexados {len(documents)} productos.")

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
        Retrieve exact product details (simulating a DB lookup via metadata here).
        In production, this might query SQL.
        """
        # Chroma metadata filtering
        results = self.vector_store.get(where={"sku": sku})
        if results and results['metadatas']:
            return results['metadatas'][0]
        return None
