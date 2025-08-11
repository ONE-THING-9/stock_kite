from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from datetime import datetime, date

class HistoricalDataRequest(BaseModel):
    stock_name: str = Field(..., description="Stock symbol or trading symbol")
    timeframe: str = Field(..., description="Timeframe: minute, day, etc.")
    from_date: date = Field(..., description="Start date for historical data")
    to_date: date = Field(..., description="End date for historical data")

class CandleData(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class HistoricalDataResponse(BaseModel):
    stock_name: str
    timeframe: str
    data: List[CandleData]
    count: int

class InstrumentMetadata(BaseModel):
    instrument_token: int
    exchange_token: int
    tradingsymbol: str
    name: str
    last_price: float
    expiry: Optional[str] = None
    strike: Optional[float] = None
    tick_size: float
    lot_size: int
    instrument_type: str
    segment: str
    exchange: str

class LiveDataRequest(BaseModel):
    stock_name: str = Field(..., description="Stock symbol or trading symbol")

class LiveQuote(BaseModel):
    instrument_token: int
    timestamp: datetime
    last_price: float
    last_quantity: int
    average_price: float
    volume: int
    buy_quantity: int
    sell_quantity: int
    ohlc: dict
    net_change: float

class LiveDataResponse(BaseModel):
    stock_name: str
    quote: LiveQuote

class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int

class MarketIndicatorsRequest(BaseModel):
    stock_name: str = Field(..., description="Stock symbol or trading symbol")
    date: Optional[date] = None

class MarketBreadthData(BaseModel):
    advances: int
    declines: int
    unchanged: int
    advance_decline_ratio: float
    advance_decline_line: float

class MarketIndicatorsData(BaseModel):
    india_vix: Optional[float] = None
    put_call_ratio: Optional[float] = None
    market_breadth: Optional[MarketBreadthData] = None
    nifty_pcr: Optional[float] = None
    data_date: date
    last_updated: datetime = Field(default_factory=datetime.now)

class MarketIndicatorsResponse(BaseModel):
    stock_name: str
    indicators: MarketIndicatorsData
    data_sources: List[str] = Field(default_factory=list)