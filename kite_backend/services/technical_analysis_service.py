import pandas as pd
import numpy as np
import ta
from datetime import datetime
from typing import List, Optional, Dict
from jinja2 import Template
from utils.logger import setup_logger
from utils.config import settings
from models.technical_analysis import (
    TechnicalAnalysisRequest, TechnicalAnalysisResponse, TimeframeAnalysis,
    MAResult, RSIResult, MACDResult, BollingerBandResult, VWAPResult,
    CandlestickPattern, PatternResult
)
from services.historical_data_service import HistoricalDataService
from services.auth_service import AuthService
from services.gemini_ai_service import GeminiAIService
from models.stock_data import HistoricalDataRequest
from models.gemini_ai import GeminiRequest

class TechnicalAnalysisService:
    def __init__(self, auth_service: AuthService):
        self.logger = setup_logger(__name__)
        self.auth_service = auth_service
        self.historical_service = HistoricalDataService(auth_service)
        self.gemini_service = GeminiAIService()
    
    def analyze_stock(self, request: TechnicalAnalysisRequest, include_gemini_opinion: bool = False) -> TechnicalAnalysisResponse:
        try:
            self.logger.info(f"Starting technical analysis for {request.stock_name}")
            
            timeframe_results = []
            
            for timeframe in request.timeframes:
                try:
                    analysis = self._analyze_timeframe(
                        request.stock_name, 
                        timeframe, 
                        request.from_date, 
                        request.to_date
                    )
                    timeframe_results.append(analysis)
                    
                except Exception as e:
                    self.logger.error(f"Error analyzing timeframe {timeframe}: {str(e)}")
                    continue
            
            if not timeframe_results:
                raise ValueError("No successful analysis for any timeframe")
            
            response = TechnicalAnalysisResponse(
                stock_name=request.stock_name,
                analysis_date=datetime.now().isoformat(),
                timeframe_results=timeframe_results,
                summary=self._generate_summary(timeframe_results)
            )
            
            # Add Gemini opinion if requested
            if include_gemini_opinion:
                try:
                    gemini_opinion = self._generate_gemini_opinion(response)
                    response.gemini_opinion = gemini_opinion
                except Exception as e:
                    self.logger.error(f"Failed to generate Gemini opinion: {str(e)}")
                    response.gemini_opinion = "Unable to generate AI opinion due to technical error."
            
            self.logger.info(f"Technical analysis completed for {request.stock_name}")
            return response
            
        except Exception as e:
            self.logger.error(f"Technical analysis failed for {request.stock_name}: {str(e)}")
            raise e
    
    def _analyze_timeframe(self, stock_name: str, timeframe: str, from_date, to_date) -> TimeframeAnalysis:
        historical_request = HistoricalDataRequest(
            stock_name=stock_name,
            timeframe=timeframe,
            from_date=from_date,
            to_date=to_date
        )
        
        historical_data = self.historical_service.get_historical_data(historical_request)
        
        if not historical_data.data or len(historical_data.data) < 50:
            raise ValueError(f"Insufficient data for analysis (got {len(historical_data.data) if historical_data.data else 0} points)")
        
        df = self._convert_to_dataframe(historical_data.data)
        
        analysis = TimeframeAnalysis(
            timeframe=timeframe,
            data_points=len(df)
        )
        
        # Calculate all indicators
        analysis.add_ma(self._calculate_ma(df, period=20))
        analysis.add_ma(self._calculate_ma(df, period=50))
        analysis.add_ema(self._calculate_ema(df, period=20))
        analysis.add_ema(self._calculate_ema(df, period=50))
        analysis.add_rsi(self._calculate_rsi(df))
        analysis.add_macd(self._calculate_macd(df))
        analysis.add_bollinger_bands(self._calculate_bollinger_bands(df))
        analysis.add_vwap(self._calculate_vwap(df))
        
        # Add candlestick pattern detection
        patterns = self._detect_all_patterns(df)
        analysis.add_candlestick_patterns(patterns)
        
        return analysis
    
    def _convert_to_dataframe(self, candle_data) -> pd.DataFrame:
        data = []
        for candle in candle_data:
            data.append({
                'timestamp': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    def _calculate_ma(self, df: pd.DataFrame, period: int = 20) -> MAResult:
        ma_values = ta.trend.sma_indicator(df['close'], window=period)
        current_value = float(ma_values.iloc[-1]) if not pd.isna(ma_values.iloc[-1]) else None
        
        # Generate signal
        current_price = float(df['close'].iloc[-1])
        signal = "BULLISH" if current_price > current_value else "BEARISH" if current_value else "NEUTRAL"
        
        return MAResult(
            name=f"SMA_{period}",
            values=ma_values.fillna(0).tolist(),
            current_value=current_value,
            signal=signal,
            period=period,
            ma_type="SMA"
        )
    
    def _calculate_ema(self, df: pd.DataFrame, period: int = 20) -> MAResult:
        ema_values = ta.trend.ema_indicator(df['close'], window=period)
        current_value = float(ema_values.iloc[-1]) if not pd.isna(ema_values.iloc[-1]) else None
        
        # Generate signal
        current_price = float(df['close'].iloc[-1])
        signal = "BULLISH" if current_price > current_value else "BEARISH" if current_value else "NEUTRAL"
        
        return MAResult(
            name=f"EMA_{period}",
            values=ema_values.fillna(0).tolist(),
            current_value=current_value,
            signal=signal,
            period=period,
            ma_type="EMA"
        )
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> RSIResult:
        rsi_values = ta.momentum.rsi(df['close'], window=period)
        current_value = float(rsi_values.iloc[-1]) if not pd.isna(rsi_values.iloc[-1]) else None
        
        # Generate signal
        signal = "NEUTRAL"
        if current_value:
            if current_value > 70:
                signal = "OVERBOUGHT"
            elif current_value < 30:
                signal = "OVERSOLD"
            elif current_value > 50:
                signal = "BULLISH"
            else:
                signal = "BEARISH"
        
        return RSIResult(
            name="RSI",
            values=rsi_values.fillna(0).tolist(),
            current_value=current_value,
            signal=signal,
            period=period
        )
    
    def _calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal_period: int = 9) -> MACDResult:
        # Calculate MACD Line: EMA(12) - EMA(26)
        macd_line = ta.trend.macd(df['close'], window_fast=fast, window_slow=slow)
        
        # Calculate Signal Line: 9-period EMA of MACD Line
        signal_line = ta.trend.macd_signal(df['close'], window_fast=fast, window_slow=slow, window_sign=signal_period)
        
        # Calculate Histogram: MACD Line - Signal Line
        histogram = ta.trend.macd_diff(df['close'], window_fast=fast, window_slow=slow, window_sign=signal_period)
        
        current_macd = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
        current_signal = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
        current_histogram = float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None
        
        # Generate signal
        signal = "NEUTRAL"
        if current_macd and current_signal:
            if current_macd > current_signal:
                signal = "BULLISH"
            else:
                signal = "BEARISH"
        
        return MACDResult(
            macd_line=macd_line.fillna(0).tolist(),
            signal_line=signal_line.fillna(0).tolist(),
            histogram=histogram.fillna(0).tolist(),
            current_macd=current_macd,
            current_signal=current_signal,
            current_histogram=current_histogram,
            signal=signal
        )
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std: float = 2.0) -> BollingerBandResult:
        # Calculate middle band (SMA)
        bb_middle = df['close'].rolling(window=period).mean()
        
        # Calculate standard deviation
        rolling_std = df['close'].rolling(window=period).std()
        
        # Calculate upper and lower bands
        bb_upper = bb_middle + (std * rolling_std)
        bb_lower = bb_middle - (std * rolling_std)
        
        current_upper = float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None
        current_middle = float(bb_middle.iloc[-1]) if not pd.isna(bb_middle.iloc[-1]) else None
        current_lower = float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None
        current_price = float(df['close'].iloc[-1])
        
        # Generate signal
        signal = "NEUTRAL"
        if current_upper and current_lower:
            if current_price > current_upper:
                signal = "OVERBOUGHT"
            elif current_price < current_lower:
                signal = "OVERSOLD"
        
        return BollingerBandResult(
            upper_band=bb_upper.fillna(0).tolist(),
            middle_band=bb_middle.fillna(0).tolist(),
            lower_band=bb_lower.fillna(0).tolist(),
            current_upper=current_upper,
            current_middle=current_middle,
            current_lower=current_lower,
            current_price=current_price,
            signal=signal
        )
    
    def _calculate_vwap(self, df: pd.DataFrame) -> VWAPResult:
        vwap_values = ta.volume.volume_weighted_average_price(
            df['high'], df['low'], df['close'], df['volume']
        )
        current_value = float(vwap_values.iloc[-1]) if not pd.isna(vwap_values.iloc[-1]) else None
        
        # Generate signal
        current_price = float(df['close'].iloc[-1])
        signal = "BULLISH" if current_price > current_value else "BEARISH" if current_value else "NEUTRAL"
        
        return VWAPResult(
            name="VWAP",
            values=vwap_values.fillna(0).tolist(),
            current_value=current_value,
            signal=signal
        )
    
    def _generate_summary(self, timeframe_results: List[TimeframeAnalysis]) -> dict:
        summary = {
            "total_timeframes": len(timeframe_results),
            "indicators_calculated": ["MA", "EMA", "RSI", "MACD", "BollingerBands", "VWAP"],
            "overall_signals": {},
            "candlestick_patterns": {}
        }
        
        # Aggregate signals across timeframes
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        
        # Aggregate patterns across timeframes
        pattern_summary = {}
        
        for tf_result in timeframe_results:
            # Process indicators
            for indicator_name, indicator_data in tf_result.indicators.items():
                signal = indicator_data.get('signal', 'NEUTRAL')
                if 'BULLISH' in signal:
                    bullish_count += 1
                elif 'BEARISH' in signal:
                    bearish_count += 1
                else:
                    neutral_count += 1
            
            # Process candlestick patterns
            for pattern_name, pattern_data in tf_result.candlestick_patterns.items():
                if pattern_data.total_count > 0:
                    if pattern_name not in pattern_summary:
                        pattern_summary[pattern_name] = {
                            'total_occurrences': 0,
                            'bullish_count': 0,
                            'bearish_count': 0,
                            'neutral_count': 0,
                            'last_occurrence': None
                        }
                    
                    pattern_summary[pattern_name]['total_occurrences'] += pattern_data.total_count
                    
                    # Count pattern types
                    for occurrence in pattern_data.occurrences:
                        pattern_type = occurrence.pattern_type
                        if pattern_type == 'bullish':
                            pattern_summary[pattern_name]['bullish_count'] += 1
                        elif pattern_type == 'bearish':
                            pattern_summary[pattern_name]['bearish_count'] += 1
                        else:
                            pattern_summary[pattern_name]['neutral_count'] += 1
                    
                    # Update last occurrence
                    if pattern_data.last_occurrence:
                        if (not pattern_summary[pattern_name]['last_occurrence'] or 
                            pattern_data.last_occurrence > pattern_summary[pattern_name]['last_occurrence']):
                            pattern_summary[pattern_name]['last_occurrence'] = pattern_data.last_occurrence
        
        # Calculate signal percentages
        total_signals = bullish_count + bearish_count + neutral_count
        if total_signals > 0:
            summary["overall_signals"] = {
                "bullish_percentage": round((bullish_count / total_signals) * 100, 2),
                "bearish_percentage": round((bearish_count / total_signals) * 100, 2),
                "neutral_percentage": round((neutral_count / total_signals) * 100, 2)
            }
        
        summary["candlestick_patterns"] = pattern_summary
        
        return summary
    
    def _generate_gemini_opinion(self, response: TechnicalAnalysisResponse) -> str:
        """
        Generate Gemini AI opinion based on technical analysis data
        """
        try:
            # Load the prompt template
            prompt_file_path = "/Users/amitkumar/Desktop/stock/kite_backend/utils/prompts/technical_analysis_prompt.txt"
            with open(prompt_file_path, 'r') as f:
                prompt_template = f.read()
            
            # Prepare historical data for template
            historical_data = []
            if response.timeframe_results:
                tf_result = response.timeframe_results[0]  # Use first timeframe for historical data
                historical_data = {
                    "timeframe": tf_result.timeframe,
                    "data_points": tf_result.data_points,
                    "stock_name": response.stock_name,
                    "analysis_date": response.analysis_date
                }
            
            # Prepare technical indicators data
            technical_indicators = {}
            if response.timeframe_results:
                for tf_result in response.timeframe_results:
                    for indicator_name, indicator_data in tf_result.indicators.items():
                        technical_indicators[f"{tf_result.timeframe}_{indicator_name}"] = {
                            "signal": indicator_data.get('signal', 'NEUTRAL'),
                            "current_value": indicator_data.get('current_value'),
                            "name": indicator_data.get('name', indicator_name)
                        }
            
            # Render the template with Jinja2
            template = Template(prompt_template)
            rendered_prompt = template.render(
                historical_data=historical_data,
                technical_indicators=technical_indicators,
                summary=response.summary
            )
            
            # Create Gemini request
            gemini_request = GeminiRequest(
                model_name=settings.gemini_model,
                prompt=rendered_prompt,
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=1000,
                top_p=0.9
            )
            
            # Get Gemini response
            gemini_response = self.gemini_service.generate_response(gemini_request)
            
            if gemini_response.status == "success":
                self.logger.info(f"Successfully generated Gemini opinion for {response.stock_name}")
                return gemini_response.response_text
            else:
                self.logger.error(f"Failed to generate Gemini opinion: {gemini_response.response_text}")
                return "Unable to generate AI opinion at this time."
                
        except Exception as e:
            self.logger.error(f"Error generating Gemini opinion: {str(e)}")
            return "Unable to generate AI opinion due to technical error."
    
    def _detect_all_patterns(self, df: pd.DataFrame) -> Dict[str, PatternResult]:
        """
        Detect all candlestick patterns in the dataframe
        """
        patterns = {}
        
        # Detect individual patterns
        patterns["hammer"] = self._detect_hammer_pattern(df)
        patterns["doji"] = self._detect_doji_pattern(df)
        patterns["marubozu"] = self._detect_marubozu_pattern(df)
        patterns["engulfing"] = self._detect_engulfing_pattern(df)
        patterns["harami"] = self._detect_harami_pattern(df)
        patterns["morning_star"] = self._detect_morning_star_pattern(df)
        
        return patterns
    
    def _detect_hammer_pattern(self, df: pd.DataFrame) -> PatternResult:
        """
        Detect Hammer candlestick pattern
        Hammer: Small body at top, long lower shadow, minimal upper shadow
        """
        patterns = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            open_price = row['open']
            high = row['high']
            low = row['low']
            close = row['close']
            
            # Calculate body and shadow lengths
            body_length = abs(close - open_price)
            total_range = high - low
            lower_shadow = min(open_price, close) - low
            upper_shadow = high - max(open_price, close)
            
            # Hammer criteria
            if total_range > 0:
                body_ratio = body_length / total_range
                lower_shadow_ratio = lower_shadow / total_range
                upper_shadow_ratio = upper_shadow / total_range
                
                # Hammer pattern conditions
                if (body_ratio < 0.3 and  # Small body
                    lower_shadow_ratio > 0.6 and  # Long lower shadow
                    upper_shadow_ratio < 0.1):  # Minimal upper shadow
                    
                    confidence = min(0.9, 0.5 + (lower_shadow_ratio - body_ratio))
                    
                    pattern = CandlestickPattern(
                        name="Hammer",
                        pattern_type="bullish",
                        confidence=confidence,
                        timestamp=str(row.name),
                        description="Bullish reversal pattern with long lower shadow",
                        candle_index=i
                    )
                    patterns.append(pattern)
        
        return PatternResult(
            pattern_name="Hammer",
            occurrences=patterns,
            total_count=len(patterns),
            last_occurrence=patterns[-1].timestamp if patterns else None
        )
    
    def _detect_doji_pattern(self, df: pd.DataFrame) -> PatternResult:
        """
        Detect Doji candlestick pattern
        Doji: Open and close are very close, indicating indecision
        """
        patterns = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            open_price = row['open']
            high = row['high']
            low = row['low']
            close = row['close']
            
            # Calculate body and total range
            body_length = abs(close - open_price)
            total_range = high - low
            
            # Doji criteria - body should be very small relative to total range
            if total_range > 0:
                body_ratio = body_length / total_range
                
                if body_ratio < 0.05:  # Body is less than 5% of total range
                    confidence = min(0.9, 0.8 - body_ratio * 10)
                    
                    pattern = CandlestickPattern(
                        name="Doji",
                        pattern_type="neutral",
                        confidence=confidence,
                        timestamp=str(row.name),
                        description="Indecision pattern with minimal body",
                        candle_index=i
                    )
                    patterns.append(pattern)
        
        return PatternResult(
            pattern_name="Doji",
            occurrences=patterns,
            total_count=len(patterns),
            last_occurrence=patterns[-1].timestamp if patterns else None
        )
    
    def _detect_marubozu_pattern(self, df: pd.DataFrame) -> PatternResult:
        """
        Detect Marubozu candlestick pattern
        Marubozu: No or minimal shadows, strong directional move
        """
        patterns = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            open_price = row['open']
            high = row['high']
            low = row['low']
            close = row['close']
            
            # Calculate body and shadow lengths
            body_length = abs(close - open_price)
            total_range = high - low
            lower_shadow = min(open_price, close) - low
            upper_shadow = high - max(open_price, close)
            
            # Marubozu criteria
            if total_range > 0:
                body_ratio = body_length / total_range
                shadow_ratio = (lower_shadow + upper_shadow) / total_range
                
                # Strong body with minimal shadows
                if body_ratio > 0.9 and shadow_ratio < 0.1:
                    pattern_type = "bullish" if close > open_price else "bearish"
                    confidence = min(0.9, body_ratio)
                    
                    pattern = CandlestickPattern(
                        name="Marubozu",
                        pattern_type=pattern_type,
                        confidence=confidence,
                        timestamp=str(row.name),
                        description=f"{pattern_type.title()} marubozu with strong directional move",
                        candle_index=i
                    )
                    patterns.append(pattern)
        
        return PatternResult(
            pattern_name="Marubozu",
            occurrences=patterns,
            total_count=len(patterns),
            last_occurrence=patterns[-1].timestamp if patterns else None
        )
    
    def _detect_engulfing_pattern(self, df: pd.DataFrame) -> PatternResult:
        """
        Detect Engulfing candlestick pattern
        Engulfing: Current candle completely engulfs the previous candle
        """
        patterns = []
        
        for i in range(1, len(df)):  # Start from 1 since we need previous candle
            current = df.iloc[i]
            previous = df.iloc[i-1]
            
            curr_open = current['open']
            curr_close = current['close']
            curr_high = current['high']
            curr_low = current['low']
            
            prev_open = previous['open']
            prev_close = previous['close']
            prev_high = previous['high']
            prev_low = previous['low']
            
            # Check if current candle engulfs previous candle
            current_bullish = curr_close > curr_open
            previous_bullish = prev_close > prev_open
            
            # Bullish engulfing: bearish candle followed by bullish candle that engulfs it
            if (not previous_bullish and current_bullish and
                curr_open < prev_close and curr_close > prev_open and
                curr_high >= prev_high and curr_low <= prev_low):
                
                # Calculate confidence based on size difference
                curr_body = abs(curr_close - curr_open)
                prev_body = abs(prev_close - prev_open)
                confidence = min(0.9, 0.6 + (curr_body / prev_body) * 0.1)
                
                pattern = CandlestickPattern(
                    name="Bullish Engulfing",
                    pattern_type="bullish",
                    confidence=confidence,
                    timestamp=str(current.name),
                    description="Bullish reversal pattern engulfing previous bearish candle",
                    candle_index=i
                )
                patterns.append(pattern)
            
            # Bearish engulfing: bullish candle followed by bearish candle that engulfs it
            elif (previous_bullish and not current_bullish and
                  curr_open > prev_close and curr_close < prev_open and
                  curr_high >= prev_high and curr_low <= prev_low):
                
                curr_body = abs(curr_close - curr_open)
                prev_body = abs(prev_close - prev_open)
                confidence = min(0.9, 0.6 + (curr_body / prev_body) * 0.1)
                
                pattern = CandlestickPattern(
                    name="Bearish Engulfing",
                    pattern_type="bearish",
                    confidence=confidence,
                    timestamp=str(current.name),
                    description="Bearish reversal pattern engulfing previous bullish candle",
                    candle_index=i
                )
                patterns.append(pattern)
        
        return PatternResult(
            pattern_name="Engulfing",
            occurrences=patterns,
            total_count=len(patterns),
            last_occurrence=patterns[-1].timestamp if patterns else None
        )
    
    def _detect_harami_pattern(self, df: pd.DataFrame) -> PatternResult:
        """
        Detect Harami candlestick pattern
        Harami: Small candle contained within the body of the previous large candle
        """
        patterns = []
        
        for i in range(1, len(df)):  # Start from 1 since we need previous candle
            current = df.iloc[i]
            previous = df.iloc[i-1]
            
            curr_open = current['open']
            curr_close = current['close']
            prev_open = previous['open']
            prev_close = previous['close']
            
            # Calculate body ranges
            curr_body_top = max(curr_open, curr_close)
            curr_body_bottom = min(curr_open, curr_close)
            prev_body_top = max(prev_open, prev_close)
            prev_body_bottom = min(prev_open, prev_close)
            
            curr_body_length = abs(curr_close - curr_open)
            prev_body_length = abs(prev_close - prev_open)
            
            # Check if current candle is contained within previous candle's body
            if (curr_body_top < prev_body_top and curr_body_bottom > prev_body_bottom and
                prev_body_length > 0 and curr_body_length / prev_body_length < 0.5):
                
                # Determine pattern type based on previous candle
                previous_bullish = prev_close > prev_open
                pattern_type = "bearish" if previous_bullish else "bullish"
                
                confidence = min(0.9, 0.7 - (curr_body_length / prev_body_length))
                
                pattern = CandlestickPattern(
                    name="Harami",
                    pattern_type=pattern_type,
                    confidence=confidence,
                    timestamp=str(current.name),
                    description=f"{pattern_type.title()} harami reversal pattern",
                    candle_index=i
                )
                patterns.append(pattern)
        
        return PatternResult(
            pattern_name="Harami",
            occurrences=patterns,
            total_count=len(patterns),
            last_occurrence=patterns[-1].timestamp if patterns else None
        )
    
    def _detect_morning_star_pattern(self, df: pd.DataFrame) -> PatternResult:
        """
        Detect Morning Star candlestick pattern
        Morning Star: Three-candle bullish reversal pattern
        1. Bearish candle
        2. Small-bodied candle (can be bullish or bearish)
        3. Bullish candle that closes above middle of first candle
        """
        patterns = []
        
        for i in range(2, len(df)):  # Start from 2 since we need two previous candles
            candle1 = df.iloc[i-2]  # First candle (bearish)
            candle2 = df.iloc[i-1]  # Middle candle (small body)
            candle3 = df.iloc[i]    # Third candle (bullish)
            
            # Extract OHLC for each candle
            c1_open, c1_close = candle1['open'], candle1['close']
            c2_open, c2_close = candle2['open'], candle2['close']
            c3_open, c3_close = candle3['open'], candle3['close']
            c2_high, c2_low = candle2['high'], candle2['low']
            
            # Calculate body lengths
            c1_body = abs(c1_close - c1_open)
            c2_body = abs(c2_close - c2_open)
            c3_body = abs(c3_close - c3_open)
            
            # Morning star conditions
            c1_bearish = c1_close < c1_open  # First candle is bearish
            c3_bullish = c3_close > c3_open  # Third candle is bullish
            c2_small = c2_body < (c1_body * 0.5)  # Middle candle has small body
            
            # Gap conditions (middle candle should gap below first, third should gap above middle)
            gap_down = c2_high < min(c1_open, c1_close)
            gap_up = c3_open > max(c2_open, c2_close)
            
            # Third candle should close above middle of first candle
            c1_middle = (c1_open + c1_close) / 2
            closes_above_middle = c3_close > c1_middle
            
            if (c1_bearish and c3_bullish and c2_small and 
                closes_above_middle and (gap_down or gap_up)):
                
                # Calculate confidence based on pattern strength
                gap_strength = 0.1 if (gap_down and gap_up) else 0.05
                body_ratio = 1 - (c2_body / max(c1_body, c3_body))
                confidence = min(0.9, 0.6 + gap_strength + body_ratio * 0.2)
                
                pattern = CandlestickPattern(
                    name="Morning Star",
                    pattern_type="bullish",
                    confidence=confidence,
                    timestamp=str(candle3.name),
                    description="Three-candle bullish reversal pattern",
                    candle_index=i
                )
                patterns.append(pattern)
        
        return PatternResult(
            pattern_name="Morning Star",
            occurrences=patterns,
            total_count=len(patterns),
            last_occurrence=patterns[-1].timestamp if patterns else None
        )