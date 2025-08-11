from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class GeminiRequest(BaseModel):
    model_name: str = Field(..., description="Gemini model name (e.g., 'gemini-pro', 'gemini-pro-vision')")
    prompt: str = Field(..., description="The prompt to send to Gemini")
    temperature: Optional[float] = Field(default=0.7, description="Controls randomness in response (0.0 to 1.0)")
    max_tokens: Optional[int] = Field(default=1000, description="Maximum number of tokens in response")
    top_p: Optional[float] = Field(default=0.9, description="Controls diversity via nucleus sampling")
    top_k: Optional[int] = Field(default=40, description="Controls diversity by limiting token choices")

class GeminiResponse(BaseModel):
    status: str
    response_text: str
    model_used: str
    token_count: Optional[int] = None
    finish_reason: Optional[str] = None
    safety_ratings: Optional[List[Dict[str, Any]]] = None

class GeminiError(BaseModel):
    error: str
    message: str
    model_name: Optional[str] = None

class ComprehensiveAnalysisRequest(BaseModel):
    historical_data: Dict[str, Any] = Field(..., description="Historical stock data")
    technical_analysis: Dict[str, Any] = Field(..., description="Technical analysis results")
    stock_symbol: str = Field(..., description="Stock symbol being analyzed")
    timeframe: str = Field(..., description="Timeframe used for analysis")
    days: int = Field(..., description="Number of days of data")
    market_indicators: Optional[Dict[str, Any]] = Field(
        default=None, description="Market indicators (VIX, PCR, breadth, etc.)"
    )