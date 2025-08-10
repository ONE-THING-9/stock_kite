# Stock Trading Dashboard Frontend

A modern, responsive web interface for visualizing stock data with candlestick charts and technical analysis indicators.

## Features

- **Candlestick Charts**: Interactive charts using Chart.js with financial chart extensions
- **Technical Analysis**: Real-time display of various technical indicators (RSI, MACD, SMA, EMA, Bollinger Bands, etc.)
- **Multiple Timeframes**: Support for 1min, 5min, 15min, 30min, 1hr, and 1day intervals
- **Dark Theme**: Professional trading platform aesthetic
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Live connection status with backend API

## Quick Start

### Prerequisites

Make sure your FastAPI backend is running:

```bash
cd ../kite_backend
pip install -r requirements.txt
python main.py
```

The backend should be accessible at `http://localhost:8000`

### Running the Frontend

#### Option 1: Using Python (Recommended)

```bash
cd frontend
python server.py
```

This will start a local server on `http://localhost:3000` and automatically open your browser.

#### Option 2: Using any HTTP server

```bash
# Using Python's built-in server
python -m http.server 3000

# Using Node.js http-server (if installed)
npx http-server -p 3000

# Using PHP (if available)
php -S localhost:3000
```

## Usage

1. **Enter Stock Symbol**: Type a stock symbol (e.g., "HDFC", "TCS", "RELIANCE")
2. **Select Timeframe**: Choose from various intervals (1min to 1day)
3. **Set Days**: Specify how many days of historical data to fetch (30-365 days)
4. **Load Data**: Click the "Load Data" button to fetch and display the chart

## Architecture

```
frontend/
├── index.html          # Main HTML structure
├── styles.css          # Professional dark theme styling
├── script.js           # JavaScript for chart rendering and API calls
├── server.py           # Simple Python HTTP server
└── README.md           # This file
```

## API Integration

The frontend connects to your FastAPI backend endpoints:

- `GET /health` - Check backend connection and auth status
- `GET /historical/{symbol}/data` - Fetch historical price data
- `GET /technical-analysis/{symbol}/quick` - Get technical analysis

## Customization

### Adding New Indicators

To add new technical indicators:

1. Update the `formatIndicatorName()` function in `script.js`
2. Modify the `keyIndicators` array in `updateIndicatorsGrid()` 
3. Ensure your backend provides the indicator data

### Styling Changes

All styling is contained in `styles.css` using CSS custom properties (variables) for easy theming:

```css
:root {
    --primary-bg: #0d1421;     /* Main background */
    --secondary-bg: #1a2332;   /* Panel backgrounds */
    --accent-blue: #2196f3;    /* Primary accent color */
    --accent-green: #00c853;   /* Positive/bullish color */
    --accent-red: #f44336;     /* Negative/bearish color */
}
```

## Browser Compatibility

- Chrome/Chromium 88+
- Firefox 85+
- Safari 14+
- Edge 88+

## Troubleshooting

### Backend Connection Issues

1. Verify the FastAPI backend is running on `http://localhost:8000`
2. Check the browser console for CORS errors
3. Ensure the backend has CORS middleware configured properly

### Chart Not Displaying

1. Check if the stock symbol is valid and available in your data source
2. Verify the selected timeframe is supported by your backend
3. Look for JavaScript errors in the browser console

### Performance Issues

1. Reduce the number of days for high-frequency timeframes (1min, 5min)
2. Use daily data for longer historical analysis
3. Consider implementing data pagination for large datasets