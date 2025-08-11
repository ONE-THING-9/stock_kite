from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from jinja2 import Template
from utils.logger import setup_logger
from utils.config import settings
from models.gemini_ai import GeminiRequest, GeminiResponse, ComprehensiveAnalysisRequest
from services.gemini_ai_service import GeminiAIService

router = APIRouter(prefix="/gemini-ai", tags=["Gemini AI"])
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

@router.post("/analyze", response_model=GeminiResponse)
async def analyze_comprehensive_data(
    request: ComprehensiveAnalysisRequest,
    gemini_service: GeminiAIService = Depends(get_gemini_service)
):
    """
    Analyze comprehensive stock data using Gemini AI
    
    This endpoint accepts historical data, technical analysis results, and other
    stock information to provide a comprehensive AI-powered analysis.
    """
    try:
        logger.info(f"Starting comprehensive AI analysis for {request.stock_symbol}")
        
        # Load the prompt template
        prompt_file_path = "/Users/amitkumar/Desktop/stock/kite_backend/utils/prompts/technical_analysis_prompt.txt"
        with open(prompt_file_path, 'r') as f:
            prompt_template = f.read()
        
        # Prepare historical data for template
        historical_data = {
            "stock_name": request.stock_symbol,
            "timeframe": request.timeframe,
            "days": request.days,
            "data_points": len(request.historical_data.get('data', [])),
            "analysis_date": request.technical_analysis.get('analysis_date', 'N/A')
        }
        
        # Prepare technical indicators data
        technical_indicators = {}
        if request.technical_analysis.get('timeframe_results'):
            for tf_result in request.technical_analysis['timeframe_results']:
                for indicator_name, indicator_data in tf_result.get('indicators', {}).items():
                    technical_indicators[f"{tf_result['timeframe']}_{indicator_name}"] = {
                        "signal": indicator_data.get('signal', 'NEUTRAL'),
                        "current_value": indicator_data.get('current_value'),
                        "name": indicator_data.get('name', indicator_name)
                    }
        
        # Get summary data
        summary = request.technical_analysis.get('summary', {})
        
        # Prepare market indicators data
        market_data = {}
        if request.market_indicators:
            market_data = {
                "india_vix": request.market_indicators.get('indicators', {}).get('india_vix'),
                "put_call_ratio": request.market_indicators.get('indicators', {}).get('put_call_ratio') or 
                                request.market_indicators.get('indicators', {}).get('nifty_pcr'),
                "market_breadth": request.market_indicators.get('indicators', {}).get('market_breadth'),
                "data_sources": request.market_indicators.get('data_sources', [])
            }
        
        # Render the template with Jinja2
        template = Template(prompt_template)
        rendered_prompt = template.render(
            historical_data=historical_data,
            technical_indicators=technical_indicators,
            summary=summary,
            market_indicators=market_data
        )
        
        logger.info(f"Generated prompt for {request.stock_symbol} (length: {len(rendered_prompt)} chars)")
        
        # Create Gemini request
        gemini_request = GeminiRequest(
            model_name=settings.gemini_model,
            prompt=rendered_prompt,
            temperature=0.3,  # Lower temperature for more consistent analysis
            max_tokens=1500,  # Increased token limit for comprehensive analysis
            top_p=0.9
        )
        
        # Get Gemini response
        response = gemini_service.generate_response(gemini_request)
        
        if response.status == "success":
            logger.info(f"Successfully generated AI analysis for {request.stock_symbol}")
            return response
        else:
            logger.error(f"Gemini AI analysis failed: {response.response_text}")
            raise HTTPException(
                status_code=500,
                detail=f"AI analysis failed: {response.response_text}"
            )
            
    except FileNotFoundError:
        logger.error("Technical analysis prompt template not found")
        raise HTTPException(
            status_code=500,
            detail="AI analysis template not found. Please check server configuration."
        )
    except Exception as e:
        logger.error(f"Error in comprehensive analysis for {request.stock_symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI analysis: {str(e)}"
        )