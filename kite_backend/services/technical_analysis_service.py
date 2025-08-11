import pandas as pd
import numpy as np
import ta
from datetime import datetime
from typing import List, Optional, Dict, Any
from jinja2 import Template
from utils.logger import setup_logger
from utils.config import settings
from models.technical_analysis import (
    TechnicalAnalysisRequest, TechnicalAnalysisResponse, TimeframeAnalysis,
    MAResult, RSIResult, MACDResult, BollingerBandResult, VWAPResult,
    CandlestickPattern, PatternResult, SupportResistanceLevel, SupportResistanceResult
)
from services.historical_data_service import HistoricalDataService
from services.auth_service import AuthService
from models.stock_data import HistoricalDataRequest

class TechnicalAnalysisService:
    def __init__(self, auth_service: AuthService):
        self.logger = setup_logger(__name__)
        self.auth_service = auth_service
        self.historical_service = HistoricalDataService(auth_service)
    
    def analyze_stock(self, request: TechnicalAnalysisRequest) -> TechnicalAnalysisResponse:
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
        analysis.add_support_resistance(self._calculate_support_resistance(df))
        
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
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> SupportResistanceResult:
        """
        Calculate support and resistance levels using multiple algorithms
        """
        current_price = float(df['close'].iloc[-1])
        
        # Combine different detection methods
        pivot_levels = self._detect_pivot_levels(df)
        horizontal_levels = self._detect_horizontal_levels(df)
        volume_levels = self._detect_volume_weighted_levels(df)
        
        # Merge and rank levels
        all_levels = pivot_levels + horizontal_levels + volume_levels
        support_levels, resistance_levels = self._classify_and_rank_levels(all_levels, current_price)
        
        # Find nearest levels
        nearest_support = self._find_nearest_level(support_levels, current_price, "below")
        nearest_resistance = self._find_nearest_level(resistance_levels, current_price, "above")
        
        # Generate price action signal
        price_action_signal = self._generate_price_action_signal(
            df, current_price, nearest_support, nearest_resistance
        )
        
        # Detect recent level breaks
        key_level_breaks = self._detect_recent_breaks(df, all_levels)
        
        return SupportResistanceResult(
            support_levels=support_levels[:5],  # Top 5 support levels
            resistance_levels=resistance_levels[:5],  # Top 5 resistance levels
            nearest_support=nearest_support,
            nearest_resistance=nearest_resistance,
            current_price=current_price,
            price_action_signal=price_action_signal,
            key_level_breaks=key_level_breaks
        )
    
    def _detect_pivot_levels(self, df: pd.DataFrame, window: int = 5) -> List[SupportResistanceLevel]:
        """
        Detect pivot points (swing highs and lows) as support/resistance levels
        """
        levels = []
        
        # Find swing highs (resistance levels)
        for i in range(window, len(df) - window):
            current_high = df['high'].iloc[i]
            left_highs = df['high'].iloc[i-window:i]
            right_highs = df['high'].iloc[i+1:i+window+1]
            
            # Check if current high is higher than surrounding highs
            if current_high > left_highs.max() and current_high > right_highs.max():
                # Calculate strength based on how much higher it is
                avg_surrounding = (left_highs.mean() + right_highs.mean()) / 2
                strength_factor = (current_high - avg_surrounding) / avg_surrounding * 100
                strength = min(10.0, max(1.0, strength_factor * 2))
                
                levels.append(SupportResistanceLevel(
                    price=current_high,
                    level_type="resistance",
                    strength=strength,
                    touches=1,
                    last_touch_timestamp=str(df.index[i]),
                    volume_at_level=float(df['volume'].iloc[i]) if 'volume' in df.columns else None,
                    distance_from_current=((current_high - df['close'].iloc[-1]) / df['close'].iloc[-1]) * 100,
                    is_dynamic=False
                ))
        
        # Find swing lows (support levels)
        for i in range(window, len(df) - window):
            current_low = df['low'].iloc[i]
            left_lows = df['low'].iloc[i-window:i]
            right_lows = df['low'].iloc[i+1:i+window+1]
            
            # Check if current low is lower than surrounding lows
            if current_low < left_lows.min() and current_low < right_lows.min():
                # Calculate strength based on how much lower it is
                avg_surrounding = (left_lows.mean() + right_lows.mean()) / 2
                strength_factor = (avg_surrounding - current_low) / avg_surrounding * 100
                strength = min(10.0, max(1.0, strength_factor * 2))
                
                levels.append(SupportResistanceLevel(
                    price=current_low,
                    level_type="support",
                    strength=strength,
                    touches=1,
                    last_touch_timestamp=str(df.index[i]),
                    volume_at_level=float(df['volume'].iloc[i]) if 'volume' in df.columns else None,
                    distance_from_current=((df['close'].iloc[-1] - current_low) / current_low) * 100,
                    is_dynamic=False
                ))
        
        return levels
    
    def _detect_horizontal_levels(self, df: pd.DataFrame, touch_threshold: float = 0.5) -> List[SupportResistanceLevel]:
        """
        Detect horizontal support/resistance levels based on price clustering
        Uses price levels that have been touched multiple times
        """
        levels = []
        
        # Get all significant price points (highs and lows)
        highs = df['high'].tolist()
        lows = df['low'].tolist()
        closes = df['close'].tolist()
        all_prices = highs + lows + closes
        
        # Remove duplicates and sort
        unique_prices = list(set(all_prices))
        unique_prices.sort()
        
        # Group nearby prices (within touch_threshold %)
        price_groups = []
        current_group = [unique_prices[0]]
        
        for price in unique_prices[1:]:
            # If price is within threshold of current group's average, add to group
            group_avg = sum(current_group) / len(current_group)
            if abs(price - group_avg) / group_avg * 100 <= touch_threshold:
                current_group.append(price)
            else:
                # Save current group if it has multiple touches
                if len(current_group) >= 2:
                    price_groups.append(current_group)
                current_group = [price]
        
        # Don't forget the last group
        if len(current_group) >= 2:
            price_groups.append(current_group)
        
        # Convert price groups to support/resistance levels
        current_price = df['close'].iloc[-1]
        
        for group in price_groups:
            level_price = sum(group) / len(group)  # Average price of the group
            touches = len(group)
            
            # Determine if it's support or resistance based on current price
            level_type = "support" if level_price < current_price else "resistance"
            
            # Calculate strength based on number of touches and recency
            strength = min(10.0, touches * 2.0)  # More touches = stronger level
            
            # Find the most recent touch
            recent_touches = []
            tolerance = level_price * touch_threshold / 100
            
            for i, row in df.iterrows():
                if (abs(row['high'] - level_price) <= tolerance or 
                    abs(row['low'] - level_price) <= tolerance or 
                    abs(row['close'] - level_price) <= tolerance):
                    recent_touches.append(str(i))
            
            last_touch = recent_touches[-1] if recent_touches else None
            
            # Calculate average volume at this level
            volume_at_level = None
            if 'volume' in df.columns and recent_touches:
                volumes = []
                for timestamp in recent_touches:
                    try:
                        idx = df.index.get_loc(timestamp) if timestamp in df.index else None
                        if idx is not None:
                            volumes.append(df['volume'].iloc[idx])
                    except:
                        continue
                volume_at_level = sum(volumes) / len(volumes) if volumes else None
            
            # Calculate distance from current price
            distance = abs(level_price - current_price) / current_price * 100
            
            levels.append(SupportResistanceLevel(
                price=level_price,
                level_type=level_type,
                strength=strength,
                touches=touches,
                last_touch_timestamp=last_touch,
                volume_at_level=volume_at_level,
                distance_from_current=distance,
                is_dynamic=False
            ))
        
        return levels
    
    def _detect_volume_weighted_levels(self, df: pd.DataFrame) -> List[SupportResistanceLevel]:
        """
        Detect support/resistance levels based on volume profile
        Areas with high volume often act as strong support/resistance
        """
        levels = []
        
        if 'volume' not in df.columns:
            return levels  # Return empty if no volume data
        
        current_price = df['close'].iloc[-1]
        
        # Create price bins for volume analysis
        price_min = df['low'].min()
        price_max = df['high'].max()
        price_range = price_max - price_min
        bin_size = price_range / 50  # 50 price bins
        
        # Calculate volume at each price level
        price_volume_map = {}
        
        for idx, row in df.iterrows():
            # For each candle, distribute volume across its price range
            candle_range = row['high'] - row['low']
            if candle_range == 0:
                # Point candle, assign all volume to that price
                price_bin = int((row['close'] - price_min) / bin_size)
                price_volume_map[price_bin] = price_volume_map.get(price_bin, 0) + row['volume']
            else:
                # Distribute volume proportionally across the candle's range
                volume_per_price = row['volume'] / candle_range
                start_bin = int((row['low'] - price_min) / bin_size)
                end_bin = int((row['high'] - price_min) / bin_size)
                
                for bin_num in range(max(0, start_bin), min(50, end_bin + 1)):
                    bin_price = price_min + (bin_num * bin_size)
                    if row['low'] <= bin_price <= row['high']:
                        price_volume_map[bin_num] = price_volume_map.get(bin_num, 0) + volume_per_price
        
        # Find high-volume areas (potential support/resistance)
        if not price_volume_map:
            return levels
            
        avg_volume = sum(price_volume_map.values()) / len(price_volume_map)
        volume_threshold = avg_volume * 1.5  # 50% above average
        
        # Find local volume maxima
        sorted_bins = sorted(price_volume_map.keys())
        
        for i, bin_num in enumerate(sorted_bins):
            volume = price_volume_map[bin_num]
            
            if volume > volume_threshold:
                # Check if this is a local maximum
                is_local_max = True
                check_range = 3  # Check 3 bins on each side
                
                for j in range(max(0, i - check_range), min(len(sorted_bins), i + check_range + 1)):
                    if j != i and sorted_bins[j] in price_volume_map:
                        if price_volume_map[sorted_bins[j]] > volume:
                            is_local_max = False
                            break
                
                if is_local_max:
                    level_price = price_min + (bin_num * bin_size)
                    level_type = "support" if level_price < current_price else "resistance"
                    
                    # Strength based on volume relative to average
                    strength = min(10.0, (volume / avg_volume) * 2.0)
                    
                    # Find touches at this level
                    touches = 0
                    recent_touch = None
                    tolerance = bin_size
                    
                    for idx, row in df.iterrows():
                        if (abs(row['high'] - level_price) <= tolerance or 
                            abs(row['low'] - level_price) <= tolerance):
                            touches += 1
                            recent_touch = str(idx)
                    
                    distance = abs(level_price - current_price) / current_price * 100
                    
                    levels.append(SupportResistanceLevel(
                        price=level_price,
                        level_type=level_type,
                        strength=strength,
                        touches=max(1, touches),
                        last_touch_timestamp=recent_touch,
                        volume_at_level=float(volume),
                        distance_from_current=distance,
                        is_dynamic=False
                    ))
        
        return levels
    
    def _classify_and_rank_levels(self, all_levels: List[SupportResistanceLevel], current_price: float) -> tuple:
        """
        Classify levels as support/resistance and rank by strength
        """
        support_levels = []
        resistance_levels = []
        
        # Remove duplicate levels (same price within 0.1%)
        unique_levels = []
        for level in all_levels:
            is_duplicate = False
            for existing in unique_levels:
                if abs(level.price - existing.price) / existing.price * 100 < 0.1:
                    # Keep the stronger level
                    if level.strength > existing.strength:
                        unique_levels.remove(existing)
                        unique_levels.append(level)
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_levels.append(level)
        
        # Classify and update distance from current price
        for level in unique_levels:
            level.distance_from_current = abs(level.price - current_price) / current_price * 100
            
            if level.price < current_price:
                level.level_type = "support"
                support_levels.append(level)
            else:
                level.level_type = "resistance"
                resistance_levels.append(level)
        
        # Sort by strength (descending)
        support_levels.sort(key=lambda x: x.strength, reverse=True)
        resistance_levels.sort(key=lambda x: x.strength, reverse=True)
        
        return support_levels, resistance_levels
    
    def _find_nearest_level(self, levels: List[SupportResistanceLevel], current_price: float, direction: str) -> Optional[SupportResistanceLevel]:
        """
        Find the nearest support or resistance level
        """
        if not levels:
            return None
        
        if direction == "below":
            # Find nearest support (below current price)
            valid_levels = [level for level in levels if level.price < current_price]
            if valid_levels:
                return max(valid_levels, key=lambda x: x.price)
        elif direction == "above":
            # Find nearest resistance (above current price)
            valid_levels = [level for level in levels if level.price > current_price]
            if valid_levels:
                return min(valid_levels, key=lambda x: x.price)
        
        return None
    
    def _generate_price_action_signal(self, df: pd.DataFrame, current_price: float, 
                                    nearest_support: Optional[SupportResistanceLevel], 
                                    nearest_resistance: Optional[SupportResistanceLevel]) -> str:
        """
        Generate price action signal based on proximity to levels
        """
        # Calculate recent price movement
        if len(df) < 5:
            return "NEUTRAL"
        
        recent_closes = df['close'].tail(5).tolist()
        price_change = (recent_closes[-1] - recent_closes[0]) / recent_closes[0] * 100
        
        # Check proximity to levels (within 2% is considered "approaching")
        proximity_threshold = 2.0
        
        if nearest_support and abs(current_price - nearest_support.price) / current_price * 100 <= proximity_threshold:
            if price_change < -1:  # Falling towards support
                return "APPROACHING_SUPPORT"
            elif current_price < nearest_support.price:  # Broke below support
                return "BREAKDOWN"
        
        if nearest_resistance and abs(current_price - nearest_resistance.price) / current_price * 100 <= proximity_threshold:
            if price_change > 1:  # Rising towards resistance
                return "APPROACHING_RESISTANCE"
            elif current_price > nearest_resistance.price:  # Broke above resistance
                return "BREAKOUT"
        
        return "NEUTRAL"
    
    def _detect_recent_breaks(self, df: pd.DataFrame, all_levels: List[SupportResistanceLevel]) -> List[Dict[str, Any]]:
        """
        Detect recent breaks of significant support/resistance levels
        """
        breaks = []
        
        if len(df) < 10:
            return breaks
        
        # Only check last 20 candles for recent breaks
        recent_df = df.tail(20)
        
        for level in all_levels:
            if level.strength < 5.0:  # Only consider strong levels
                continue
            
            # Check if price crossed the level recently
            for i in range(1, len(recent_df)):
                current_row = recent_df.iloc[i]
                previous_row = recent_df.iloc[i-1]
                
                current_close = current_row['close']
                previous_close = previous_row['close']
                
                # Check for breakout (support became resistance or vice versa)
                if level.level_type == "support":
                    # Support break: previous close above, current close below
                    if previous_close > level.price and current_close < level.price:
                        breaks.append({
                            "timestamp": str(current_row.name),
                            "level_price": level.price,
                            "break_type": "breakdown",
                            "significance": level.strength,
                            "price_at_break": current_close
                        })
                elif level.level_type == "resistance":
                    # Resistance break: previous close below, current close above
                    if previous_close < level.price and current_close > level.price:
                        breaks.append({
                            "timestamp": str(current_row.name),
                            "level_price": level.price,
                            "break_type": "breakout",
                            "significance": level.strength,
                            "price_at_break": current_close
                        })
        
        # Sort by significance (most significant first)
        breaks.sort(key=lambda x: x['significance'], reverse=True)
        return breaks[:3]  # Return top 3 most significant recent breaks
    
    def _generate_summary(self, timeframe_results: List[TimeframeAnalysis]) -> dict:
        summary = {
            "total_timeframes": len(timeframe_results),
            "indicators_calculated": ["MA", "EMA", "RSI", "MACD", "BollingerBands", "VWAP", "SupportResistance"],
            "overall_signals": {},
            "candlestick_patterns": {},
            "support_resistance_summary": {}
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
        
        # Aggregate support/resistance data
        sr_summary = {
            "total_support_levels": 0,
            "total_resistance_levels": 0,
            "strongest_support": None,
            "strongest_resistance": None,
            "price_action_signals": {},
            "recent_breaks": []
        }
        
        for tf_result in timeframe_results:
            sr_data = tf_result.indicators.get("SupportResistance", {})
            if sr_data:
                # Count levels
                support_levels = sr_data.get("support_levels", [])
                resistance_levels = sr_data.get("resistance_levels", [])
                sr_summary["total_support_levels"] += len(support_levels)
                sr_summary["total_resistance_levels"] += len(resistance_levels)
                
                # Track strongest levels
                if support_levels:
                    strongest_support = max(support_levels, key=lambda x: x.get("strength", 0))
                    if (sr_summary["strongest_support"] is None or 
                        strongest_support.get("strength", 0) > sr_summary["strongest_support"].get("strength", 0)):
                        sr_summary["strongest_support"] = strongest_support
                
                if resistance_levels:
                    strongest_resistance = max(resistance_levels, key=lambda x: x.get("strength", 0))
                    if (sr_summary["strongest_resistance"] is None or 
                        strongest_resistance.get("strength", 0) > sr_summary["strongest_resistance"].get("strength", 0)):
                        sr_summary["strongest_resistance"] = strongest_resistance
                
                # Aggregate price action signals
                signal = sr_data.get("price_action_signal", "NEUTRAL")
                sr_summary["price_action_signals"][tf_result.timeframe] = signal
                
                # Collect recent breaks
                breaks = sr_data.get("key_level_breaks", [])
                for break_info in breaks:
                    break_info["timeframe"] = tf_result.timeframe
                    sr_summary["recent_breaks"].append(break_info)
        
        # Sort recent breaks by significance
        sr_summary["recent_breaks"].sort(key=lambda x: x.get("significance", 0), reverse=True)
        sr_summary["recent_breaks"] = sr_summary["recent_breaks"][:5]  # Top 5 most significant
        
        summary["support_resistance_summary"] = sr_summary
        
        return summary
    
    
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