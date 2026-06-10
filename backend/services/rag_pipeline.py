import os
import chromadb
import google.generativeai as genai
from typing import List, Dict, Any

class RAGPipelineService:
    def __init__(self):
        # Configure Gemini API for Embeddings
        genai.configure(api_key=os.getenv("GEMINI_API_KEY", "MOCK_KEY"))
        self.embedding_model = "models/text-embedding-004"
        
        # Initialize Persistent ChromaDB Client
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(
            name="company_policies"
        )

    def _get_embedding(self, text: str) -> List[float]:
        """Generates a text embedding vector using the Gemini API."""
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                contents=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception:
            # Safe local fallback vector dimension if key is unconfigured during initial tests
            return [0.0] * 768

    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """Inserts text chunks and metadata embeddings directly into ChromaDB."""
        embeddings = [self._get_embedding(t) for t in texts]
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )

    def search_policies(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Queries the vector base to return top relevant policy context maps."""
        query_vector = self._get_embedding(query)
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=limit
        )
        
        formatted_results = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "score": results['distances'][0][i] if results['distances'] else 0.0
                })
        return formatted_results