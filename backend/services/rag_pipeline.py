import os
import chromadb
import google.generativeai as genai
from typing import List, Dict, Any
from backend.config import settings

# 1. THE PATH FIX: Guarantee we always hit the exact same folder from the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "chroma_db")

class RAGPipelineService:
    def __init__(self):
        # Configure Gemini API for Embeddings
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.embedding_model = "models/gemini-embedding-001"
        
        # Initialize Persistent ChromaDB Client with absolute path
        self.chroma_client = chromadb.PersistentClient(path=DB_PATH)
        self.collection = self.chroma_client.get_or_create_collection(name="company_policies")

    def _get_embedding(self, text: str) -> List[float]:
        """Generates a text embedding vector using the Gemini API."""
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            # 2. THE SCORE FIX: Print the actual error so we know why it's falling back to zeros!
            print(f"❌ [GEMINI EMBEDDING ERROR] {str(e)}")
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
        
        # Explicitly ask Chroma to return the distances array
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
            include=["documents", "metadatas", "distances"] 
        )
        
        formatted_results = []
        if results and results.get('documents'):
            for i in range(len(results['documents'][0])):
                # Grab the actual mathematical distance distance
                score = results['distances'][0][i] if results.get('distances') else 0.0
                
                formatted_results.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results.get('metadatas') else {},
                    "score": round(score, 4)  # Round it so it looks clean in the API
                })
        return formatted_results