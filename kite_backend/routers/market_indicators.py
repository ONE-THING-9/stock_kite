from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import date, datetime
from models.stock_data import MarketIndicatorsRequest, MarketIndicatorsResponse
from services.market_indicators_service import MarketIndicatorsService
from services.auth_service import AuthService
from routers.auth import get_auth_service
from utils.logger import setup_logger

router = APIRouter(prefix="/market-indicators", tags=["Market Indicators"])
logger = setup_logger(__name__)

def get_market_indicators_service(auth_service: AuthService = Depends(get_auth_service)) -> MarketIndicatorsService:
    return MarketIndicatorsService(auth_service)

@router.get("/{stock_name}", response_model=MarketIndicatorsResponse)
async def get_market_indicators(
    stock_name: str,
    date: Optional[date] = Query(default=None, description="Date for market indicators (YYYY-MM-DD format, defaults to current date)"),
    service: MarketIndicatorsService = Depends(get_market_indicators_service)
):
    """
    Get comprehensive market indicators for Indian markets including:
    - India VIX (Volatility Index)
    - Put/Call Ratio (PCR)
    - Market Breadth Indicators (ADL, Advance/Decline)
    - Nifty specific PCR
    
    Args:
        stock_name: Stock symbol (used for context, indicators are market-wide)
        date: Optional date for historical data (defaults to current date)
    
    Returns:
        MarketIndicatorsResponse with all available market indicators
    """
    try:
        logger.info(f"Market indicators request for {stock_name} on {date or 'current date'}")
        
        request = MarketIndicatorsRequest(
            stock_name=stock_name,
            date=date
        )
        
        response = service.get_market_indicators(request)
        
        logger.info(f"Successfully fetched market indicators for {stock_name}")
        return response
        
    except ValueError as ve:
        logger.error(f"Validation error for market indicators {stock_name}: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error fetching market indicators for {stock_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch market indicators: {str(e)}")

@router.get("/", response_model=MarketIndicatorsResponse)
async def get_current_market_indicators(
    stock_name: str = Query(..., description="Stock symbol for context"),
    service: MarketIndicatorsService = Depends(get_market_indicators_service)
):
    """
    Get current market indicators for Indian markets (convenience endpoint)
    
    Args:
        stock_name: Stock symbol (used for context, indicators are market-wide)
    
    Returns:
        MarketIndicatorsResponse with current market indicators
    """
    try:
        logger.info(f"Current market indicators request for {stock_name}")
        
        request = MarketIndicatorsRequest(
            stock_name=stock_name,
            date=None  # Will default to current date
        )
        
        response = service.get_market_indicators(request)
        
        logger.info(f"Successfully fetched current market indicators for {stock_name}")
        return response
        
    except ValueError as ve:
        logger.error(f"Validation error for current market indicators {stock_name}: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error fetching current market indicators for {stock_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch current market indicators: {str(e)}")

@router.get("/health/check")
async def health_check():
    """
    Health check endpoint for market indicators service
    """
    try:
        # Test basic service initialization
        service = MarketIndicatorsService()
        
        return {
            "status": "healthy",
            "service": "market_indicators",
            "timestamp": datetime.now(),
            "available_indicators": [
                "india_vix",
                "put_call_ratio", 
                "market_breadth",
                "nifty_pcr"
            ]
        }
        
    except Exception as e:
        logger.error(f"Market indicators service health check failed: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail=f"Market indicators service unhealthy: {str(e)}"
        )