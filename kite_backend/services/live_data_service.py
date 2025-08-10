from kiteconnect import KiteConnect
from datetime import datetime
from typing import List, Optional, Dict
from utils.logger import setup_logger
from models.stock_data import LiveDataRequest, LiveDataResponse, LiveQuote
from services.auth_service import AuthService

class LiveDataService:
    def __init__(self, auth_service: AuthService):
        self.logger = setup_logger(__name__)
        self.auth_service = auth_service
        self.kite: Optional[KiteConnect] = None
        self._instruments_cache = None
    
    def _get_kite_instance(self) -> Optional[KiteConnect]:
        self.kite = self.auth_service.get_kite_instance()
        return self.kite
    
    def _get_instrument_token(self, stock_name: str) -> Optional[int]:
        try:
            if not self._get_kite_instance():
                self.logger.error("Kite instance not available")
                return None
            
            if not self._instruments_cache:
                self._instruments_cache = self.kite.instruments()
            
            for instrument in self._instruments_cache:
                if (instrument['tradingsymbol'].upper() == stock_name.upper() or 
                    instrument['name'].upper() == stock_name.upper()):
                    return instrument['instrument_token']
            
            self.logger.warning(f"Instrument token not found for stock: {stock_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding instrument token for {stock_name}: {str(e)}")
            return None
    
    def get_live_data(self, request: LiveDataRequest) -> LiveDataResponse:
        try:
            if not self._get_kite_instance():
                raise ValueError("Authentication required. Kite instance not available.")
            
            instrument_token = self._get_instrument_token(request.stock_name)
            if not instrument_token:
                raise ValueError(f"Stock '{request.stock_name}' not found")
            
            self.logger.info(f"Fetching live data for {request.stock_name} ({instrument_token})")
            
            quotes = self.kite.quote([instrument_token])
            
            if str(instrument_token) not in quotes:
                raise ValueError(f"No live data available for {request.stock_name}")
            
            quote_data = quotes[str(instrument_token)]
            
            live_quote = LiveQuote(
                instrument_token=instrument_token,
                timestamp=datetime.now(),
                last_price=quote_data.get('last_price', 0.0),
                last_quantity=quote_data.get('last_quantity', 0),
                average_price=quote_data.get('average_price', 0.0),
                volume=quote_data.get('volume', 0),
                buy_quantity=quote_data.get('buy_quantity', 0),
                sell_quantity=quote_data.get('sell_quantity', 0),
                ohlc=quote_data.get('ohlc', {}),
                net_change=quote_data.get('net_change', 0.0)
            )
            
            response = LiveDataResponse(
                stock_name=request.stock_name,
                quote=live_quote
            )
            
            self.logger.info(
                f"Successfully fetched live data for {request.stock_name}: "
                f"LTP={live_quote.last_price}, Volume={live_quote.volume}"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error fetching live data for {request.stock_name}: {str(e)}")
            raise e
    
    def get_multiple_quotes(self, stock_names: List[str]) -> Dict[str, LiveDataResponse]:
        try:
            if not self._get_kite_instance():
                raise ValueError("Authentication required. Kite instance not available.")
            
            instrument_tokens = []
            token_to_stock = {}
            
            for stock_name in stock_names:
                token = self._get_instrument_token(stock_name)
                if token:
                    instrument_tokens.append(token)
                    token_to_stock[str(token)] = stock_name
                else:
                    self.logger.warning(f"Skipping {stock_name} - instrument token not found")
            
            if not instrument_tokens:
                raise ValueError("No valid instruments found for the provided stock names")
            
            self.logger.info(f"Fetching live data for {len(instrument_tokens)} instruments")
            
            quotes = self.kite.quote(instrument_tokens)
            
            results = {}
            for token_str, quote_data in quotes.items():
                stock_name = token_to_stock[token_str]
                
                live_quote = LiveQuote(
                    instrument_token=int(token_str),
                    timestamp=datetime.now(),
                    last_price=quote_data.get('last_price', 0.0),
                    last_quantity=quote_data.get('last_quantity', 0),
                    average_price=quote_data.get('average_price', 0.0),
                    volume=quote_data.get('volume', 0),
                    buy_quantity=quote_data.get('buy_quantity', 0),
                    sell_quantity=quote_data.get('sell_quantity', 0),
                    ohlc=quote_data.get('ohlc', {}),
                    net_change=quote_data.get('net_change', 0.0)
                )
                
                results[stock_name] = LiveDataResponse(
                    stock_name=stock_name,
                    quote=live_quote
                )
            
            self.logger.info(f"Successfully fetched live data for {len(results)} stocks")
            return results
            
        except Exception as e:
            self.logger.error(f"Error fetching multiple quotes: {str(e)}")
            raise e