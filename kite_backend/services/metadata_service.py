from kiteconnect import KiteConnect
from typing import List, Optional
from utils.logger import setup_logger
from models.stock_data import InstrumentMetadata
from services.auth_service import AuthService

class MetadataService:
    def __init__(self, auth_service: AuthService):
        self.logger = setup_logger(__name__)
        self.auth_service = auth_service
        self.kite: Optional[KiteConnect] = None
        self._instruments_cache = None
    
    def _get_kite_instance(self) -> Optional[KiteConnect]:
        self.kite = self.auth_service.get_kite_instance()
        return self.kite
    
    def _load_instruments(self) -> List[dict]:
        try:
            if not self._get_kite_instance():
                raise ValueError("Authentication required. Kite instance not available.")
            
            if not self._instruments_cache:
                self.logger.info("Loading instruments data from Kite Connect")
                self._instruments_cache = self.kite.instruments()
                self.logger.info(f"Loaded {len(self._instruments_cache)} instruments")
            
            return self._instruments_cache
            
        except Exception as e:
            self.logger.error(f"Error loading instruments: {str(e)}")
            raise e
    
    def get_instrument_metadata(self, stock_name: str) -> InstrumentMetadata:
        try:
            instruments = self._load_instruments()
            
            matching_instrument = None
            for instrument in instruments:
                if (instrument['tradingsymbol'].upper() == stock_name.upper() or 
                    instrument['name'].upper() == stock_name.upper()):
                    matching_instrument = instrument
                    break
            
            if not matching_instrument:
                raise ValueError(f"Stock '{stock_name}' not found")
            
            self.logger.info(f"Found metadata for {stock_name}: {matching_instrument['tradingsymbol']}")
            
            return InstrumentMetadata(
                instrument_token=matching_instrument['instrument_token'],
                exchange_token=matching_instrument['exchange_token'],
                tradingsymbol=matching_instrument['tradingsymbol'],
                name=matching_instrument['name'],
                last_price=matching_instrument.get('last_price', 0.0),
                expiry=matching_instrument.get('expiry'),
                strike=matching_instrument.get('strike'),
                tick_size=matching_instrument.get('tick_size', 0.05),
                lot_size=matching_instrument.get('lot_size', 1),
                instrument_type=matching_instrument.get('instrument_type', ''),
                segment=matching_instrument.get('segment', ''),
                exchange=matching_instrument.get('exchange', '')
            )
            
        except Exception as e:
            self.logger.error(f"Error getting metadata for {stock_name}: {str(e)}")
            raise e
    
    def search_instruments(self, query: str) -> List[InstrumentMetadata]:
        try:
            instruments = self._load_instruments()
            
            matching_instruments = []
            query_upper = query.upper()
            
            for instrument in instruments:
                if (query_upper in instrument['tradingsymbol'].upper() or 
                    query_upper in instrument['name'].upper()):
                    
                    metadata = InstrumentMetadata(
                        instrument_token=instrument['instrument_token'],
                        exchange_token=instrument['exchange_token'],
                        tradingsymbol=instrument['tradingsymbol'],
                        name=instrument['name'],
                        last_price=instrument.get('last_price', 0.0),
                        expiry=instrument.get('expiry'),
                        strike=instrument.get('strike'),
                        tick_size=instrument.get('tick_size', 0.05),
                        lot_size=instrument.get('lot_size', 1),
                        instrument_type=instrument.get('instrument_type', ''),
                        segment=instrument.get('segment', ''),
                        exchange=instrument.get('exchange', '')
                    )
                    matching_instruments.append(metadata)
                    
                    if len(matching_instruments) >= 20:
                        break
            
            self.logger.info(f"Found {len(matching_instruments)} instruments matching '{query}'")
            return matching_instruments
            
        except Exception as e:
            self.logger.error(f"Error searching instruments with query '{query}': {str(e)}")
            raise e
    
    def refresh_instruments_cache(self) -> bool:
        try:
            self._instruments_cache = None
            self._load_instruments()
            self.logger.info("Instruments cache refreshed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error refreshing instruments cache: {str(e)}")
            return False