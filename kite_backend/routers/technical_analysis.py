from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import date
from typing import List
from models.technical_analysis import TechnicalAnalysisRequest, TechnicalAnalysisResponse, TechnicalAnalysisError
from services.technical_analysis_service import TechnicalAnalysisService
from services.auth_service import AuthService
from routers.auth import get_auth_service
from utils.logger import setup_logger

router = APIRouter(prefix="/technical-analysis", tags=["Technical Analysis"])
logger = setup_logger(__name__)

def get_technical_analysis_service(auth_service: AuthService = Depends(get_auth_service)) -> TechnicalAnalysisService:
    return TechnicalAnalysisService(auth_service)

@router.post("/{stock_name}", response_model=TechnicalAnalysisResponse)
async def analyze_stock_technical(
    stock_name: str,
    timeframes: List[str] = Query(..., description="List of timeframes (e.g., ['1day', '1hour', '30minute'])"),
    from_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    service: TechnicalAnalysisService = Depends(get_technical_analysis_service)
):
    try:
        logger.info(f"Technical analysis request for {stock_name}, timeframes: {timeframes}")
        
        # Validate timeframes
        valid_timeframes = [
            "1minute", "3minute", "5minute", "10minute", "15minute", 
            "30minute", "1hour", "1day", "minute", "day"
        ]
        
        invalid_timeframes = [tf for tf in timeframes if tf not in valid_timeframes]
        if invalid_timeframes:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid timeframes: {invalid_timeframes}. Valid options: {valid_timeframes}"
            )
        
        request = TechnicalAnalysisRequest(
            stock_name=stock_name,
            timeframes=timeframes,
            from_date=from_date,
            to_date=to_date
        )
        
        response = service.analyze_stock(request)
        return response
        
    except ValueError as ve:
        logger.error(f"Validation error for {stock_name}: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in technical analysis for {stock_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{stock_name}/quick", response_model=TechnicalAnalysisResponse)
async def quick_technical_analysis(
    stock_name: str,
    timeframe: str = Query("1day", description="Single timeframe for analysis"),
    days: int = Query(100, description="Number of days of historical data", ge=30, le=365),
    service: TechnicalAnalysisService = Depends(get_technical_analysis_service)
):
    try:
        logger.info(f"Quick technical analysis for {stock_name}, timeframe: {timeframe}")
        
        # Calculate from_date based on days parameter
        from datetime import datetime, timedelta
        to_date_calc = datetime.now().date()
        from_date_calc = to_date_calc - timedelta(days=days)
        
        request = TechnicalAnalysisRequest(
            stock_name=stock_name,
            timeframes=[timeframe],
            from_date=from_date_calc,
            to_date=to_date_calc
        )
        
        response = service.analyze_stock(request, include_gemini_opinion=True)
        return response
        
    except ValueError as ve:
        logger.error(f"Validation error for {stock_name}: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in quick technical analysis for {stock_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))