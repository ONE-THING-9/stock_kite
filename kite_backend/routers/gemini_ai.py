from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from utils.logger import setup_logger
from models.gemini_ai import GeminiRequest, GeminiResponse
from services.gemini_ai_service import GeminiAIService

router = APIRouter(prefix="/gemini", tags=["Gemini AI"])
logger = setup_logger(__name__)

def get_gemini_service() -> GeminiAIService:
    """Dependency to get Gemini AI service instance"""
    try:
        return GeminiAIService()
    except Exception as e:
        logger.error(f"Failed to initialize Gemini AI service: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Gemini AI service not available. Please check API key configuration."
        )

@router.post("/generate", response_model=GeminiResponse)
async def generate_content(
    request: GeminiRequest,
    gemini_service: GeminiAIService = Depends(get_gemini_service)
):
    """
    Generate content using Gemini AI
    
    - **model_name**: Gemini model to use (e.g., 'gemini-pro', 'gemini-pro-vision')
    - **prompt**: The prompt to send to the AI
    - **temperature**: Controls randomness (0.0 to 1.0, default 0.7)
    - **max_tokens**: Maximum response length (default 1000)
    - **top_p**: Nucleus sampling parameter (default 0.9)
    - **top_k**: Top-k sampling parameter (default 40)
    """
    try:
        logger.info(f"Generating content for model: {request.model_name}")
        logger.info(f"Prompt preview: {request.prompt[:100]}{'...' if len(request.prompt) > 100 else ''}")
        
        response = gemini_service.generate_response(request)
        
        if response.status == "error":
            raise HTTPException(status_code=400, detail=response.response_text)
        
        logger.info("Content generated successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_content endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/models")
async def list_models(
    gemini_service: GeminiAIService = Depends(get_gemini_service)
) -> List[Dict[str, Any]]:
    """
    List available Gemini models
    """
    try:
        logger.info("Fetching available Gemini models")
        models = gemini_service.list_available_models()
        logger.info(f"Found {len(models)} available models")
        return models
        
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch models: {str(e)}"
        )

@router.post("/chat", response_model=GeminiResponse)
async def chat_with_gemini(
    request: GeminiRequest,
    gemini_service: GeminiAIService = Depends(get_gemini_service)
):
    """
    Chat with Gemini AI (alias for generate endpoint with conversational defaults)
    """
    # Set more conversational defaults
    if request.temperature is None:
        request.temperature = 0.9
    if request.model_name == "":
        request.model_name = "gemini-pro"
    
    return await generate_content(request, gemini_service)