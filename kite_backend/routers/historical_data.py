from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import date
from models.stock_data import HistoricalDataRequest, HistoricalDataResponse, ErrorResponse
from services.historical_data_service import HistoricalDataService
from services.auth_service import AuthService
from routers.auth import get_auth_service
from utils.logger import setup_logger

router = APIRouter(prefix="/historical", tags=["Historical Data"])
logger = setup_logger(__name__)

def get_historical_service(auth_service: AuthService = Depends(get_auth_service)) -> HistoricalDataService:
    return HistoricalDataService(auth_service)

@router.get("/{stock_name}", response_model=HistoricalDataResponse)
async def get_historical_data(
    stock_name: str,
    timeframe: str = Query(..., description="Timeframe (e.g., 1minute, 5minute, 1day)"),
    from_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    service: HistoricalDataService = Depends(get_historical_service)
):
    try:
        logger.info(f"Historical data request for {stock_name}, {timeframe}, {from_date} to {to_date}")
        
        request = HistoricalDataRequest(
            stock_name=stock_name,
            timeframe=timeframe,
            from_date=from_date,
            to_date=to_date
        )
        
        response = service.get_historical_data(request)
        return response
        
    except ValueError as ve:
        logger.error(f"Validation error for {stock_name}: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error fetching historical data for {stock_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))