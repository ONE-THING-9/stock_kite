# Claude Code Trading System

A comprehensive multi-agent trading analysis system built for Claude Code subagents that provides intelligent day trading recommendations through deep analysis of technical indicators, volume patterns, and market sentiment.

## 🚀 Features

### Multi-Agent Architecture
- **Data Requirements Agent**: Determines optimal data requirements based on strategy and market conditions
- **Data Fetcher Agent**: Interfaces with Kite MCP to retrieve market data with fallback mock data
- **Technical Analysis Agent**: Performs comprehensive technical analysis including patterns, trends, and support/resistance
- **Indicator Analysis Agent**: Calculates and analyzes technical indicators (RSI, MACD, Bollinger Bands, etc.)
- **Volume Analysis Agent**: Analyzes volume patterns, liquidity, and accumulation/distribution
- **Sentiment Analysis Agent**: Processes market sentiment from price action, news, and social media
- **Decision Maker Agent**: Uses deep thinking to synthesize all analysis into BUY/SELL/HOLD decisions
- **Orchestrator Agent**: Coordinates the entire workflow and manages agent communication

### Advanced Analysis Capabilities
- **Technical Patterns**: Double tops/bottoms, triangles, head and shoulders
- **Volume Analysis**: Volume profile, unusual volume detection, orderbook analysis
- **Risk Assessment**: Volatility analysis, position sizing, stop-loss calculation
- **Sentiment Integration**: Price action sentiment, news analysis, market breadth
- **Deep Thinking**: Multi-factor confluence analysis with detailed reasoning

### Trading Strategy Support
- **Day Trading**: 5m-30m timeframes with momentum and breakout focus
- **Scalping**: 1m-5m timeframes with high-frequency signals
- **Swing Trading**: 15m-1d timeframes for longer-term positions
- **Momentum Trading**: Focus on trending moves with strong volume
- **Breakout Trading**: Pattern-based entries with volatility expansion

## 📁 Project Structure

```
trading-system/
├── agents/                          # All trading agents
│   ├── data_requirements.py         # Determines data needs
│   ├── data_fetcher.py              # Fetches market data via Kite MCP
│   ├── technical_analysis.py        # Technical analysis and patterns
│   ├── indicator_analysis.py        # Technical indicators calculation
│   ├── volume_analysis.py           # Volume and liquidity analysis
│   ├── sentiment_analysis.py        # Market sentiment analysis
│   ├── decision_maker.py            # Final decision making with deep thinking
│   └── orchestrator.py              # Workflow coordination
├── config/                          # Configuration files
│   ├── agent_configs.json           # Agent-specific configurations
│   └── trading_parameters.json      # Trading strategy parameters
├── utils/                           # Utility functions
│   ├── data_processor.py            # Data processing utilities
│   └── risk_manager.py              # Risk management functions
├── main.py                          # Main entry point
└── README.md                        # This file
```

## 🛠 Setup & Installation

### Prerequisites
- Python 3.8+
- Claude Code environment
- Kite Connect API access (optional - system works with mock data)

### Installation
1. Clone or create the project structure as shown above
2. Ensure all agent files are in the `agents/` directory
3. Configure your trading parameters in `config/trading_parameters.json`
4. Set up Kite API credentials in `config/agent_configs.json` (optional)

### Configuration
1. **Kite API Setup** (Optional):
   ```json
   "kite_config": {
     "api_key": "your_kite_api_key_here",
     "access_token": "your_access_token_here"
   }
   ```

2. **Trading Parameters**:
   - Modify risk levels in `config/trading_parameters.json`
   - Adjust strategy-specific parameters
   - Configure symbol preferences

## 📊 Usage

### Basic Usage
```python
from agents.orchestrator import run_trading_analysis

# Run analysis with default parameters
results = run_trading_analysis(
    symbols=['RELIANCE', 'TCS', 'INFY'],
    strategy='day_trading',
    risk_appetite='medium',
    capital=100000,
    include_sentiment=True
)
```

### Command Line Interface
```bash
# Run default analysis
python main.py

# Run custom analysis with user inputs
python main.py custom

# Check system status
python main.py status

# Show help
python main.py help
```

### Advanced Usage
```python
from agents.orchestrator import TradingOrchestrator

orchestrator = TradingOrchestrator()

trading_request = {
    'symbols': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK'],
    'trading_strategy': 'momentum',
    'risk_appetite': 'high',
    'capital_available': 500000,
    'include_sentiment': True,
    'max_positions': 8,
    'risk_per_trade': 0.025
}

results = orchestrator.execute_trading_analysis(trading_request)
```

## 🔍 Analysis Output

### Executive Summary
- Market condition and sentiment overview
- Trading signals breakdown (BUY/SELL/HOLD)
- Top opportunities with confidence scores
- Portfolio allocation recommendations
- Key market insights

### Detailed Analysis
- Technical analysis for each symbol
- Indicator signals and momentum scores
- Volume patterns and liquidity assessment
- Sentiment scores from multiple sources
- Risk metrics and position sizing

### Trading Decisions
- BUY/SELL/HOLD recommendations with confidence
- Entry/exit price levels
- Stop-loss and take-profit targets
- Position sizing based on risk parameters
- Detailed reasoning for each decision

## 🎯 Example Output

```
📊 MARKET OVERVIEW
  Condition: BULLISH
  Risk Level: MEDIUM
  Sentiment: SLIGHTLY_BULLISH
  Volume Health: HEALTHY
  Recommended Exposure: 75%

📈 TRADING SIGNALS
  Total Symbols Analyzed: 5
  Buy Signals: 2
  Sell Signals: 1
  Hold Signals: 2
  Actionable Opportunities: 3

🎯 TOP OPPORTUNITIES
  1. RELIANCE: BUY (Confidence: 0.8, Score: 0.72)
  2. TCS: SELL (Confidence: 0.7, Score: 0.65)
  3. INFY: BUY (Confidence: 0.6, Score: 0.54)
```

## ⚙️ Agent Details

### Data Requirements Agent
- Analyzes trading strategy and market conditions
- Determines optimal timeframes and indicators
- Selects appropriate symbols based on risk appetite
- Optimizes data fetching to minimize API calls

### Data Fetcher Agent
- Interfaces with Kite Connect API
- Implements intelligent caching system
- Provides mock data for development/testing
- Handles API errors and rate limiting

### Technical Analysis Agent
- Identifies chart patterns and trends
- Calculates support/resistance levels
- Analyzes price action and candlestick patterns
- Generates confluence-based signals

### Indicator Analysis Agent
- Calculates 10+ technical indicators
- Provides overbought/oversold signals
- Tracks momentum and trend strength
- Cross-timeframe indicator analysis

### Volume Analysis Agent
- Analyzes volume profile and distribution
- Detects unusual volume and accumulation
- Assesses liquidity and market depth
- Provides volume confirmation signals

### Sentiment Analysis Agent
- Derives sentiment from price action
- Analyzes market breadth indicators
- Processes news and social media (when available)
- Combines multiple sentiment sources

### Decision Maker Agent
- Deep thinking analysis process
- Multi-factor confluence scoring
- Risk-adjusted position sizing
- Detailed reasoning for decisions

### Orchestrator Agent
- Coordinates all agents in proper sequence
- Manages parallel execution for performance
- Provides comprehensive error handling
- Generates executive summaries

## 🔧 Customization

### Adding New Indicators
1. Extend the `IndicatorAnalysisAgent` class
2. Implement calculation method
3. Add signal generation logic
4. Update configuration files

### Creating New Strategies
1. Define strategy parameters in `trading_parameters.json`
2. Update `DataRequirementsAgent` strategy mapping
3. Adjust decision criteria in `DecisionMakerAgent`

### Integrating External Data
1. Extend `DataFetcherAgent` with new data sources
2. Update `SentimentAnalysisAgent` for new sentiment sources
3. Modify orchestrator workflow as needed

## 📈 Performance Features

- **Parallel Processing**: Analysis agents run concurrently
- **Intelligent Caching**: Reduces redundant API calls
- **Error Recovery**: Continues analysis even if some agents fail
- **Scalable Architecture**: Easy to add new agents or data sources

## 🛡 Risk Management

- **Position Sizing**: Kelly Criterion and fixed fractional methods
- **Stop Losses**: Technical and ATR-based stop levels
- **Risk Limits**: Per-trade and portfolio risk controls
- **Volatility Adjustment**: Position sizes adjusted for volatility

## 🔍 Monitoring & Logging

- **Execution Logging**: Detailed workflow execution logs
- **Performance Metrics**: Analysis timing and success rates
- **Error Tracking**: Comprehensive error logging
- **Status Monitoring**: Real-time system status checks

## 🤝 Contributing

This system is designed for the Claude Code environment. To extend or modify:

1. Follow the existing agent pattern with `execute_[agent]_task()` functions
2. Maintain error handling and logging standards
3. Update configuration files for new parameters
4. Test with mock data before live trading

## ⚠️ Disclaimer

This system is for educational and research purposes. Always:
- Test thoroughly before live trading
- Use proper risk management
- Understand the risks of algorithmic trading
- Comply with relevant regulations

## 📞 Support

For issues or questions about the Claude Code Trading System:
- Review the execution logs for debugging
- Check configuration files for proper setup
- Ensure all dependencies are properly installed
- Test with mock data first before live trading

---

**Built for Claude Code - Intelligent Trading Analysis at Scale** 🚀