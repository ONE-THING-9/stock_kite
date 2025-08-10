from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import date

class TechnicalAnalysisRequest(BaseModel):
    stock_name: str = Field(..., description="Stock symbol or trading symbol")
    timeframes: List[str] = Field(..., description="List of timeframes (e.g., ['1day', '1hour', '30minute'])")
    from_date: date = Field(..., description="Start date for analysis")
    to_date: date = Field(..., description="End date for analysis")

class IndicatorResult(BaseModel):
    name: str
    values: List[float]
    current_value: Optional[float] = None
    signal: Optional[str] = None

class MAResult(IndicatorResult):
    period: int
    ma_type: str  # "SMA" or "EMA"

class RSIResult(IndicatorResult):
    period: int
    overbought_level: float = 70.0
    oversold_level: float = 30.0

class MACDResult(BaseModel):
    name: str = "MACD"
    macd_line: List[float]
    signal_line: List[float]
    histogram: List[float]
    current_macd: Optional[float] = None
    current_signal: Optional[float] = None
    current_histogram: Optional[float] = None
    signal: Optional[str] = None

class BollingerBandResult(BaseModel):
    name: str = "Bollinger Bands"
    upper_band: List[float]
    middle_band: List[float]  # SMA
    lower_band: List[float]
    current_upper: Optional[float] = None
    current_middle: Optional[float] = None
    current_lower: Optional[float] = None
    current_price: Optional[float] = None
    signal: Optional[str] = None

class VWAPResult(IndicatorResult):
    pass

class CandlestickPattern(BaseModel):
    name: str
    pattern_type: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0.0 to 1.0
    timestamp: str
    description: str
    candle_index: int

class PatternResult(BaseModel):
    pattern_name: str
    occurrences: List[CandlestickPattern]
    total_count: int
    last_occurrence: Optional[str] = None

class TimeframeAnalysis(BaseModel):
    timeframe: str
    data_points: int
    indicators: Dict[str, Any] = {}
    candlestick_patterns: Dict[str, PatternResult] = {}
    
    def add_ma(self, result: MAResult):
        self.indicators[f"MA_{result.period}"] = result.dict()
    
    def add_ema(self, result: MAResult):
        self.indicators[f"EMA_{result.period}"] = result.dict()
    
    def add_rsi(self, result: RSIResult):
        self.indicators["RSI"] = result.dict()
    
    def add_macd(self, result: MACDResult):
        self.indicators["MACD"] = result.dict()
    
    def add_bollinger_bands(self, result: BollingerBandResult):
        self.indicators["BollingerBands"] = result.dict()
    
    def add_vwap(self, result: VWAPResult):
        self.indicators["VWAP"] = result.dict()
    
    def add_candlestick_patterns(self, patterns: Dict[str, PatternResult]):
        self.candlestick_patterns = patterns

class TechnicalAnalysisResponse(BaseModel):
    stock_name: str
    analysis_date: str
    timeframe_results: List[TimeframeAnalysis]
    summary: Dict[str, Any] = {}
    gemini_opinion: Optional[str] = None

class TechnicalAnalysisError(BaseModel):
    error: str
    message: str
    timeframe: Optional[str] = None