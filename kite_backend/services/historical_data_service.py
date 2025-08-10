from kiteconnect import KiteConnect
from datetime import datetime
from typing import List, Optional
from utils.logger import setup_logger
from models.stock_data import HistoricalDataRequest, HistoricalDataResponse, CandleData
from services.auth_service import AuthService

class HistoricalDataService:
    def __init__(self, auth_service: AuthService):
        self.logger = setup_logger(__name__)
        self.auth_service = auth_service
        self.kite: Optional[KiteConnect] = None
    
    def _get_kite_instance(self) -> Optional[KiteConnect]:
        self.kite = self.auth_service.get_kite_instance()
        return self.kite
    
    def _get_instrument_token(self, stock_name: str) -> Optional[int]:
        try:
            if not self._get_kite_instance():
                self.logger.error("Kite instance not available")
                return None
            
            instruments = self.kite.instruments()
            
            for instrument in instruments:
                if (instrument['tradingsymbol'].upper() == stock_name.upper() or 
                    instrument['name'].upper() == stock_name.upper()):
                    return instrument['instrument_token']
            
            self.logger.warning(f"Instrument token not found for stock: {stock_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding instrument token for {stock_name}: {str(e)}")
            return None
    
    def _convert_timeframe(self, timeframe: str) -> str:
        timeframe_mapping = {
            "1minute": "minute",
            "3minute": "3minute",
            "5minute": "5minute",
            "10minute": "10minute",
            "15minute": "15minute",
            "30minute": "30minute",
            "1hour": "60minute",
            "1day": "day",
            "daily": "day"
        }
        return timeframe_mapping.get(timeframe.lower(), timeframe)
    
    def get_historical_data(self, request: HistoricalDataRequest) -> HistoricalDataResponse:
        try:
            if not self._get_kite_instance():
                raise ValueError("Authentication required. Kite instance not available.")
            
            instrument_token = self._get_instrument_token(request.stock_name)
            if not instrument_token:
                raise ValueError(f"Stock '{request.stock_name}' not found")
            
            converted_timeframe = self._convert_timeframe(request.timeframe)
            
            self.logger.info(
                f"Fetching historical data for {request.stock_name} "
                f"({instrument_token}) from {request.from_date} to {request.to_date} "
                f"with timeframe {converted_timeframe}"
            )
            
            historical_data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=request.from_date,
                to_date=request.to_date,
                interval=converted_timeframe
            )
            
            candle_data = []
            for record in historical_data:
                candle = CandleData(
                    timestamp=record['date'],
                    open=record['open'],
                    high=record['high'],
                    low=record['low'],
                    close=record['close'],
                    volume=record['volume']
                )
                candle_data.append(candle)
            
            response = HistoricalDataResponse(
                stock_name=request.stock_name,
                timeframe=request.timeframe,
                data=candle_data,
                count=len(candle_data)
            )
            
            self.logger.info(f"Successfully fetched {len(candle_data)} records for {request.stock_name}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {request.stock_name}: {str(e)}")
            raise e