from fastapi import APIRouter, Query, HTTPException, status
from backend.services.rag_pipeline import RAGPipelineService
from typing import List, Dict, Any

router = APIRouter(prefix="/api/rag", tags=["RAG Diagnostics"])
rag_service = RAGPipelineService()

@router.get("/search", response_model=List[Dict[str, Any]])
def search_knowledge_base(
    q: str = Query(..., description="The semantic search query for internal policy docs")
):
    """
    Debug endpoint to verify document chunk relevance and similarity distance metrics.
    """
    if not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string parameter 'q' cannot be empty."
        )
    
    try:
        # Retrieve top 3 matching policy chunks [cite: 103]
        results = rag_service.search_policies(query=q, limit=3)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector database retrieval fault: {str(e)}"
        )