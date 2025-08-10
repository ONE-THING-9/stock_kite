from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from models.stock_data import InstrumentMetadata
from services.metadata_service import MetadataService
from services.auth_service import AuthService
from routers.auth import get_auth_service
from utils.logger import setup_logger

router = APIRouter(prefix="/metadata", tags=["Metadata"])
logger = setup_logger(__name__)

def get_metadata_service(auth_service: AuthService = Depends(get_auth_service)) -> MetadataService:
    return MetadataService(auth_service)

@router.get("/{stock_name}", response_model=InstrumentMetadata)
async def get_instrument_metadata(
    stock_name: str,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        logger.info(f"Metadata request for {stock_name}")
        
        metadata = service.get_instrument_metadata(stock_name)
        return metadata
        
    except ValueError as ve:
        logger.error(f"Validation error for {stock_name}: {str(ve)}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error fetching metadata for {stock_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{query}", response_model=List[InstrumentMetadata])
async def search_instruments(
    query: str,
    limit: int = Query(20, description="Maximum number of results", le=100),
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        logger.info(f"Search request for query: '{query}' with limit {limit}")
        
        instruments = service.search_instruments(query)
        
        return instruments[:limit]
        
    except Exception as e:
        logger.error(f"Error searching instruments with query '{query}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh")
async def refresh_instruments_cache(
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        logger.info("Refreshing instruments cache")
        
        success = service.refresh_instruments_cache()
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to refresh instruments cache")
        
        return {"status": "success", "message": "Instruments cache refreshed"}
        
    except Exception as e:
        logger.error(f"Error refreshing instruments cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))