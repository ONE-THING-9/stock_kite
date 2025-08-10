from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict
from models.stock_data import LiveDataRequest, LiveDataResponse
from services.live_data_service import LiveDataService
from services.auth_service import AuthService
from routers.auth import get_auth_service
from utils.logger import setup_logger

router = APIRouter(prefix="/live", tags=["Live Data"])
logger = setup_logger(__name__)

def get_live_data_service(auth_service: AuthService = Depends(get_auth_service)) -> LiveDataService:
    return LiveDataService(auth_service)

@router.get("/{stock_name}", response_model=LiveDataResponse)
async def get_live_data(
    stock_name: str,
    service: LiveDataService = Depends(get_live_data_service)
):
    try:
        logger.info(f"Live data request for {stock_name}")
        
        request = LiveDataRequest(stock_name=stock_name)
        response = service.get_live_data(request)
        
        return response
        
    except ValueError as ve:
        logger.error(f"Validation error for {stock_name}: {str(ve)}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error fetching live data for {stock_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/multiple", response_model=Dict[str, LiveDataResponse])
async def get_multiple_live_data(
    stock_names: List[str],
    service: LiveDataService = Depends(get_live_data_service)
):
    try:
        if not stock_names:
            raise HTTPException(status_code=400, detail="Stock names list cannot be empty")
        
        if len(stock_names) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 stocks allowed per request")
        
        logger.info(f"Multiple live data request for {len(stock_names)} stocks")
        
        response = service.get_multiple_quotes(stock_names)
        
        return response
        
    except ValueError as ve:
        logger.error(f"Validation error for multiple stocks: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error fetching multiple live data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))