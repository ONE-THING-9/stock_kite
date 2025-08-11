// Trading Dashboard v2 - Fixed Plotly Integration
class TradingDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.chart = null;
        this.currentData = null;
        this.loginUrl = null;
        this.currentAnalysisData = null;
        this.currentMarketIndicators = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkBackendStatus();
        this.initializeChart();
        
        // Make instance globally accessible for dropdown functionality
        window.tradingDashboard = this;
        
        // Debug: Check if modal elements exist
        console.log('Modal elements check:');
        console.log('loginModal:', document.getElementById('loginModal'));
        console.log('getLoginUrl:', document.getElementById('getLoginUrl'));
        console.log('step1:', document.getElementById('step1'));
    }

    setupEventListeners() {
        document.getElementById('loadData').addEventListener('click', () => this.loadStockData());
        document.getElementById('chatWithAI').addEventListener('click', () => this.chatWithAI());
        
        // Allow Enter key to trigger data loading
        document.getElementById('stockSymbol').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.loadStockData();
        });

        // Login functionality
        document.getElementById('loginBtn').addEventListener('click', () => {
            console.log('Login button clicked');
            this.showLoginModal();
        });
        document.getElementById('closeModal').addEventListener('click', () => this.hideLoginModal());
        document.getElementById('getLoginUrl').addEventListener('click', () => {
            console.log('Get Login URL button clicked');
            this.getLoginUrl();
        });
        document.getElementById('openKiteLogin').addEventListener('click', () => this.openKiteLogin());
        document.getElementById('submitToken').addEventListener('click', () => this.submitRequestToken());
        document.getElementById('retryLogin').addEventListener('click', () => this.resetLoginModal());

        // Allow Enter key in request token input
        document.getElementById('requestToken').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.submitRequestToken();
        });

        // Close modal when clicking outside
        document.getElementById('loginModal').addEventListener('click', (e) => {
            if (e.target.id === 'loginModal') this.hideLoginModal();
        });

        // Indicator toggle event listeners
        document.getElementById('showSMA20').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showSMA50').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showEMA20').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showEMA50').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showBB').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showVWAP').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showSupportResistance').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showRSI').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showMACD').addEventListener('change', () => this.updateChartIndicators());
        
        // Pattern radio button event listeners
        document.getElementById('showHammer').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showDoji').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showMarubozu').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showEngulfing').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showHarami').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showMorningStar').addEventListener('change', () => this.updateChartIndicators());
    }

    async checkBackendStatus() {
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        const loginBtn = document.getElementById('loginBtn');

        console.log('Checking backend status...');
        console.log('Login button element:', loginBtn);

        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const data = await response.json();
            
            console.log('Backend health response:', data);
            
            if (response.ok && data.status === 'healthy') {
                statusIndicator.classList.add('connected');
                
                console.log('Backend health data:', JSON.stringify(data, null, 2));
                console.log('Authentication status:', data.authentication);
                console.log('Auth status detail:', data.auth_status);
                
                if (data.authentication) {
                    statusText.textContent = 'Connected & Authenticated';
                    loginBtn.style.display = 'none';
                    console.log('Already authenticated, hiding login button');
                } else {
                    statusText.textContent = 'Connected (Not Authenticated)';
                    loginBtn.style.display = 'block';
                    console.log('Not authenticated, showing login button');
                }
            } else {
                statusText.textContent = 'Backend Error';
                // Show login button even on error for testing
                loginBtn.style.display = 'block';
                console.log('Backend error, showing login button for testing');
            }
        } catch (error) {
            statusText.textContent = 'Backend Offline';
            // Show login button even when offline for testing
            loginBtn.style.display = 'block';
            console.log('Backend offline, showing login button for testing');
            console.error('Backend connection failed:', error);
        }
    }

    initializeChart() {
        console.log('Initializing chart, Plotly available:', typeof Plotly);
        
        const layout = {
            title: {
                text: '',
                font: { color: '#ffffff' }
            },
            plot_bgcolor: '#1a2332',
            paper_bgcolor: '#1a2332',
            font: { color: '#b3c5d7' },
            xaxis: {
                type: 'date',
                rangeslider: { visible: false },
                gridcolor: '#3a4553',
                tickfont: { color: '#b3c5d7' },
                showgrid: true
            },
            yaxis: {
                title: 'Price (₹)',
                gridcolor: '#3a4553',
                tickfont: { color: '#b3c5d7' },
                showgrid: true,
                tickformat: '₹.2f'
            },
            margin: { l: 60, r: 20, t: 20, b: 50 },
            showlegend: false
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        // Initialize with empty data
        const data = [{
            type: 'candlestick',
            x: [],
            open: [],
            high: [],
            low: [],
            close: [],
            increasing: { line: { color: '#00c853' } },
            decreasing: { line: { color: '#f44336' } },
            showlegend: false
        }];

        Plotly.newPlot('candlestickChart', data, layout, config);
        console.log('Chart initialized successfully');
    }

    showLoading(show = true) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.add('show');
        } else {
            overlay.classList.remove('show');
        }
    }

    async loadStockData() {
        const stockSymbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
        const timeframe = document.getElementById('timeframe').value;
        const days = parseInt(document.getElementById('days').value);

        if (!stockSymbol) {
            alert('Please enter a stock symbol');
            return;
        }

        this.showLoading(true);

        try {
            // Calculate from_date and to_date
            const toDate = new Date();
            const fromDate = new Date();
            fromDate.setDate(toDate.getDate() - days);
            
            const fromDateStr = fromDate.toISOString().split('T')[0]; // YYYY-MM-DD format
            const toDateStr = toDate.toISOString().split('T')[0];

            console.log(`Fetching data for ${stockSymbol}: ${fromDateStr} to ${toDateStr}, timeframe: ${timeframe}`);

            // First get historical data - corrected endpoint
            const historicalResponse = await fetch(`${this.apiBaseUrl}/historical/${stockSymbol}?timeframe=${timeframe}&from_date=${fromDateStr}&to_date=${toDateStr}`);
            
            if (!historicalResponse.ok) {
                const errorData = await historicalResponse.json();
                throw new Error(errorData.detail || 'Failed to fetch historical data');
            }

            const historicalData = await historicalResponse.json();

            // Then get technical analysis
            const analysisResponse = await fetch(`${this.apiBaseUrl}/technical-analysis/${stockSymbol}/quick?timeframe=${timeframe}&days=${days}`);
            
            let analysisData = null;
            if (analysisResponse.ok) {
                analysisData = await analysisResponse.json();
            }

            // Get market indicators
            let marketIndicatorsData = null;
            try {
                const marketResponse = await fetch(`${this.apiBaseUrl}/market-indicators/${stockSymbol}`);
                if (marketResponse.ok) {
                    marketIndicatorsData = await marketResponse.json();
                    console.log('Market indicators data:', marketIndicatorsData);
                }
            } catch (error) {
                console.warn('Failed to fetch market indicators:', error);
            }

            this.updateChart(historicalData, stockSymbol);
            this.updateAnalysis(analysisData, stockSymbol);
            this.updateChartTitle(stockSymbol, historicalData);
            
            // Store analysis data for indicator overlays
            this.currentAnalysisData = analysisData;
            
            // Store market indicators data for AI analysis
            this.currentMarketIndicators = marketIndicatorsData;
            
            // Update patterns display
            this.updatePatternsDisplay(analysisData);

            // Update market indicators display
            this.updateMarketIndicators(marketIndicatorsData, stockSymbol);

            // Update support/resistance display
            this.updateSupportResistanceDisplay(analysisData, stockSymbol);

            // Enable Chat with AI button when data is loaded
            document.getElementById('chatWithAI').disabled = false;

        } catch (error) {
            console.error('Error loading data:', error);
            alert(`Error loading data: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    updateChart(data, symbol) {
        if (!data || !data.data || !Array.isArray(data.data)) {
            console.error('Invalid data format received');
            return;
        }

        console.log('Updating chart with data:', data.data.length, 'points');
        console.log('Sample data point:', data.data[0]);

        this.currentData = data;
        
        // Use the new integrated approach
        const plotData = this.buildPlotData();
        const layout = this.buildChartLayout();
        
        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],  // Keep pan2d for scrolling
            displaylogo: false,
            scrollZoom: true,  // Enable scroll zoom
            doubleClick: 'reset+autosize'  // Double click to reset zoom
        };

        Plotly.react('candlestickChart', plotData, layout, config);
        console.log('Chart updated successfully');
    }

    updateChartIndicators() {
        if (!this.currentData || !this.currentAnalysisData) {
            console.log('No data available for indicators');
            return;
        }

        console.log('Updating chart indicators...');
        
        const plotData = this.buildPlotData();
        const layout = this.buildChartLayout();
        
        Plotly.react('candlestickChart', plotData, layout);
    }

    buildPlotData() {
        const symbol = this.getCurrentSymbol();
        const dates = this.currentData.data.map(item => new Date(item.timestamp));
        const rawOpens = this.currentData.data.map(item => item.open);
        const rawCloses = this.currentData.data.map(item => item.close);
        const highs = this.currentData.data.map(item => item.high);
        const lows = this.currentData.data.map(item => item.low);
        
        // Calculate average price range to determine minimum body height
        const priceRanges = this.currentData.data.map(item => Math.abs(item.high - item.low));
        const avgPriceRange = priceRanges.reduce((a, b) => a + b, 0) / priceRanges.length;
        const minBodyHeight = avgPriceRange * 0.5; // Minimum 50% of average daily range - much more prominent
        
        // Enhance candlestick bodies to make them MUCH more visible
        const opens = rawOpens.map((open, index) => {
            const close = rawCloses[index];
            const bodyHeight = Math.abs(close - open);
            
            // Always ensure minimum body height for visibility
            const targetBodyHeight = Math.max(bodyHeight, minBodyHeight);
            
            if (close >= open) {
                // Green candle - expand symmetrically around midpoint
                const midpoint = (open + close) / 2;
                return midpoint - (targetBodyHeight / 2);
            } else {
                // Red candle - expand symmetrically around midpoint
                const midpoint = (open + close) / 2;
                return midpoint + (targetBodyHeight / 2);
            }
        });
        
        const closes = rawCloses.map((close, index) => {
            const open = rawOpens[index];
            const bodyHeight = Math.abs(close - open);
            
            // Always ensure minimum body height for visibility
            const targetBodyHeight = Math.max(bodyHeight, minBodyHeight);
            
            if (close >= open) {
                // Green candle - expand symmetrically around midpoint
                const midpoint = (open + close) / 2;
                return midpoint + (targetBodyHeight / 2);
            } else {
                // Red candle - expand symmetrically around midpoint
                const midpoint = (open + close) / 2;
                return midpoint - (targetBodyHeight / 2);
            }
        });

        // Base candlestick data - much thicker candles like reference image
        const plotData = [{
            type: 'candlestick',
            x: dates,
            open: opens,
            high: highs,
            low: lows,
            close: closes,
            increasing: { 
                line: { color: '#00c853', width: 3 },
                fillcolor: '#00c853'
            },
            decreasing: { 
                line: { color: '#f44336', width: 3 },
                fillcolor: '#f44336'
            },
            name: symbol,
            yaxis: 'y',
            showlegend: false,
            whiskerwidth: 2.0,  // Much thicker wicks
            // Make the candlestick bodies much wider
            xgap: 0.2,  // Increase gap slightly to make candles appear thinner
            ygap: 0
        }];

        // Add volume bars as separate subplot at bottom
        const volumes = this.currentData.data.map(item => item.volume || 0);

        const volumeColors = this.currentData.data.map((item, index) => {
            if (index === 0) return 'rgba(100, 100, 100, 0.6)';
            return rawCloses[index] >= rawOpens[index] ? 'rgba(0, 200, 83, 0.6)' : 'rgba(244, 67, 54, 0.6)';
        });

        // Add volume as separate subplot at bottom
        plotData.push({
            type: 'bar',
            x: dates,
            y: volumes,
            name: 'Volume',
            marker: {
                color: volumeColors,
                line: {
                    width: 0
                }
            },
            yaxis: 'y2',  // Separate volume axis
            showlegend: false,
            hoverinfo: 'x+text',
            text: volumes.map(v => `Vol: ${(v/1000000).toFixed(1)}M`)
        });

        // Add technical indicators if available
        if (this.currentAnalysisData && this.currentAnalysisData.timeframe_results) {
            const indicators = this.currentAnalysisData.timeframe_results[0].indicators;
            const patterns = this.currentAnalysisData.timeframe_results[0].candlestick_patterns;
            
            // Moving Averages
            if (document.getElementById('showSMA20').checked && indicators.MA_20) {
                this.addMovingAverage(plotData, dates, indicators.MA_20, 'SMA(20)', '#ff9800', 'y');
            }
            
            if (document.getElementById('showSMA50').checked && indicators.MA_50) {
                this.addMovingAverage(plotData, dates, indicators.MA_50, 'SMA(50)', '#9c27b0', 'y');
            }
            
            if (document.getElementById('showEMA20').checked && indicators.EMA_20) {
                this.addMovingAverage(plotData, dates, indicators.EMA_20, 'EMA(20)', '#2196f3', 'y');
            }
            
            if (document.getElementById('showEMA50').checked && indicators.EMA_50) {
                this.addMovingAverage(plotData, dates, indicators.EMA_50, 'EMA(50)', '#009688', 'y');
            }
            
            // Bollinger Bands
            if (document.getElementById('showBB').checked && indicators.BollingerBands) {
                this.addBollingerBands(plotData, dates, indicators.BollingerBands);
            }
            
            // VWAP
            if (document.getElementById('showVWAP').checked && indicators.VWAP) {
                this.addMovingAverage(plotData, dates, indicators.VWAP, 'VWAP', '#795548', 'y');
            }
            
            // Support & Resistance
            if (document.getElementById('showSupportResistance').checked && indicators.SupportResistance) {
                this.addSupportResistanceLevels(plotData, dates, indicators.SupportResistance);
            }
            
            // Oscillators (RSI, MACD) - these need subplots
            if (document.getElementById('showRSI').checked && indicators.RSI) {
                this.addRSI(plotData, dates, indicators.RSI);
            }
            
            if (document.getElementById('showMACD').checked && indicators.MACD) {
                this.addMACD(plotData, dates, indicators.MACD);
            }
            
            // Add candlestick patterns - check which radio button is selected
            const selectedPattern = this.getSelectedPattern();
            if (selectedPattern && patterns) {
                this.addCandlestickPatterns(plotData, dates, patterns, selectedPattern);
            }
        }

        return plotData;
    }

    addMovingAverage(plotData, dates, indicator, name, color, yaxis) {
        // Filter out zero values
        const validData = indicator.values.map((value, index) => ({
            date: dates[index],
            value: value > 0 ? value : null
        })).filter(item => item.value !== null);

        if (validData.length > 0) {
            plotData.push({
                type: 'scatter',
                mode: 'lines',
                x: validData.map(item => item.date),
                y: validData.map(item => item.value),
                name: name,
                line: { color: color, width: 2 },
                yaxis: yaxis,
                showlegend: true
            });
        }
    }

    addBollingerBands(plotData, dates, bb) {
        // Filter valid data
        const validIndices = bb.upper_band.map((value, index) => value > 0 ? index : null).filter(i => i !== null);
        
        if (validIndices.length > 0) {
            const validDates = validIndices.map(i => dates[i]);
            const upperBand = validIndices.map(i => bb.upper_band[i]);
            const middleBand = validIndices.map(i => bb.middle_band[i]);
            const lowerBand = validIndices.map(i => bb.lower_band[i]);

            // Fill between upper and lower bands (add first so lines appear on top)
            plotData.push({
                type: 'scatter',
                mode: 'none',
                x: [...validDates, ...validDates.slice().reverse()],
                y: [...upperBand, ...lowerBand.slice().reverse()],
                fill: 'toself',
                fillcolor: 'rgba(158, 158, 158, 0.05)',
                line: { color: 'transparent' },
                showlegend: false,
                hoverinfo: 'skip',
                yaxis: 'y'
            });

            // Upper band
            plotData.push({
                type: 'scatter',
                mode: 'lines',
                x: validDates,
                y: upperBand,
                name: 'BB Upper',
                line: { color: '#87CEEB', width: 1.5, dash: 'dash' },
                yaxis: 'y',
                showlegend: true
            });

            // Middle band (SMA)
            plotData.push({
                type: 'scatter',
                mode: 'lines',
                x: validDates,
                y: middleBand,
                name: 'BB Middle',
                line: { color: '#FFA500', width: 2 },
                yaxis: 'y',
                showlegend: true
            });

            // Lower band
            plotData.push({
                type: 'scatter',
                mode: 'lines',
                x: validDates,
                y: lowerBand,
                name: 'BB Lower',
                line: { color: '#87CEEB', width: 1.5, dash: 'dash' },
                yaxis: 'y',
                showlegend: true
            });
        }
    }

    addRSI(plotData, dates, rsi) {
        const validData = rsi.values.map((value, index) => ({
            date: dates[index],
            value: value > 0 ? value : null
        })).filter(item => item.value !== null);

        if (validData.length > 0) {
            plotData.push({
                type: 'scatter',
                mode: 'lines',
                x: validData.map(item => item.date),
                y: validData.map(item => item.value),
                name: 'RSI',
                line: { color: '#e91e63', width: 2 },
                yaxis: 'y3',
                showlegend: true
            });
        }
    }

    addMACD(plotData, dates, macd) {
        const validIndices = macd.macd_line.map((value, index) => value !== 0 ? index : null).filter(i => i !== null);
        const hasRSI = document.getElementById('showRSI').checked;
        const macdYAxis = hasRSI ? 'y4' : 'y3';
        
        if (validIndices.length > 0) {
            const validDates = validIndices.map(i => dates[i]);
            
            // MACD Line
            plotData.push({
                type: 'scatter',
                mode: 'lines',
                x: validDates,
                y: validIndices.map(i => macd.macd_line[i]),
                name: 'MACD',
                line: { color: '#2196f3', width: 2 },
                yaxis: macdYAxis,
                showlegend: true
            });

            // Signal Line
            plotData.push({
                type: 'scatter',
                mode: 'lines',
                x: validDates,
                y: validIndices.map(i => macd.signal_line[i]),
                name: 'MACD Signal',
                line: { color: '#ff9800', width: 2 },
                yaxis: macdYAxis,
                showlegend: true
            });

            // Histogram
            plotData.push({
                type: 'bar',
                x: validDates,
                y: validIndices.map(i => macd.histogram[i]),
                name: 'MACD Histogram',
                marker: { color: 'rgba(158, 158, 158, 0.6)' },
                yaxis: macdYAxis,
                showlegend: true
            });
        }
    }

    addSupportResistanceLevels(plotData, dates, srData) {
        if (!srData || (!srData.support_levels && !srData.resistance_levels)) {
            return;
        }

        // Get price range for better level positioning
        const prices = this.currentData.data.map(item => item.close);
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const priceRange = maxPrice - minPrice;

        // Add support levels
        if (srData.support_levels && srData.support_levels.length > 0) {
            srData.support_levels.forEach((level, index) => {
                const opacity = Math.min(1.0, level.strength / 10); // Strength-based opacity
                const lineWidth = Math.max(1, level.strength / 2); // Strength-based line width
                
                plotData.push({
                    type: 'scatter',
                    mode: 'lines',
                    x: [dates[0], dates[dates.length - 1]],
                    y: [level.price, level.price],
                    name: `Support ${level.price.toFixed(2)} (${level.strength.toFixed(1)})`,
                    line: {
                        color: `rgba(0, 200, 83, ${opacity})`,
                        width: lineWidth,
                        dash: 'solid'
                    },
                    hovertemplate: `<b>Support Level</b><br>` +
                                 `Price: ₹%{y}<br>` +
                                 `Strength: ${level.strength.toFixed(1)}/10<br>` +
                                 `Touches: ${level.touches}<br>` +
                                 `Distance: ${level.distance_from_current.toFixed(2)}%<br>` +
                                 `Type: ${level.is_dynamic ? 'Dynamic' : 'Static'}<br>` +
                                 `<extra></extra>`,
                    yaxis: 'y',
                    showlegend: true,
                    legendgroup: 'support'
                });

                // Add touch points if available
                if (level.last_touch_timestamp) {
                    const touchDate = new Date(level.last_touch_timestamp);
                    plotData.push({
                        type: 'scatter',
                        mode: 'markers',
                        x: [touchDate],
                        y: [level.price],
                        name: `S-Touch ${level.price.toFixed(2)}`,
                        marker: {
                            symbol: 'triangle-up',
                            size: 8,
                            color: 'rgba(0, 200, 83, 0.8)',
                            line: {
                                width: 1,
                                color: '#00c853'
                            }
                        },
                        hovertemplate: `<b>Support Touch</b><br>` +
                                     `Price: ₹%{y}<br>` +
                                     `Date: %{x}<br>` +
                                     `<extra></extra>`,
                        yaxis: 'y',
                        showlegend: false
                    });
                }
            });
        }

        // Add resistance levels
        if (srData.resistance_levels && srData.resistance_levels.length > 0) {
            srData.resistance_levels.forEach((level, index) => {
                const opacity = Math.min(1.0, level.strength / 10); // Strength-based opacity
                const lineWidth = Math.max(1, level.strength / 2); // Strength-based line width
                
                plotData.push({
                    type: 'scatter',
                    mode: 'lines',
                    x: [dates[0], dates[dates.length - 1]],
                    y: [level.price, level.price],
                    name: `Resistance ${level.price.toFixed(2)} (${level.strength.toFixed(1)})`,
                    line: {
                        color: `rgba(244, 67, 54, ${opacity})`,
                        width: lineWidth,
                        dash: 'solid'
                    },
                    hovertemplate: `<b>Resistance Level</b><br>` +
                                 `Price: ₹%{y}<br>` +
                                 `Strength: ${level.strength.toFixed(1)}/10<br>` +
                                 `Touches: ${level.touches}<br>` +
                                 `Distance: ${level.distance_from_current.toFixed(2)}%<br>` +
                                 `Type: ${level.is_dynamic ? 'Dynamic' : 'Static'}<br>` +
                                 `<extra></extra>`,
                    yaxis: 'y',
                    showlegend: true,
                    legendgroup: 'resistance'
                });

                // Add touch points if available
                if (level.last_touch_timestamp) {
                    const touchDate = new Date(level.last_touch_timestamp);
                    plotData.push({
                        type: 'scatter',
                        mode: 'markers',
                        x: [touchDate],
                        y: [level.price],
                        name: `R-Touch ${level.price.toFixed(2)}`,
                        marker: {
                            symbol: 'triangle-down',
                            size: 8,
                            color: 'rgba(244, 67, 54, 0.8)',
                            line: {
                                width: 1,
                                color: '#f44336'
                            }
                        },
                        hovertemplate: `<b>Resistance Touch</b><br>` +
                                     `Price: ₹%{y}<br>` +
                                     `Date: %{x}<br>` +
                                     `<extra></extra>`,
                        yaxis: 'y',
                        showlegend: false
                    });
                }
            });
        }

        // Add current price line for reference
        const currentPrice = srData.current_price;
        if (currentPrice) {
            plotData.push({
                type: 'scatter',
                mode: 'lines',
                x: [dates[0], dates[dates.length - 1]],
                y: [currentPrice, currentPrice],
                name: `Current Price ₹${currentPrice.toFixed(2)}`,
                line: {
                    color: 'rgba(255, 255, 255, 0.5)',
                    width: 1,
                    dash: 'dot'
                },
                hovertemplate: `<b>Current Price</b><br>Price: ₹%{y}<br><extra></extra>`,
                yaxis: 'y',
                showlegend: true,
                legendgroup: 'current'
            });
        }
    }

    buildChartLayout() {
        const symbol = this.getCurrentSymbol();
        const hasRSI = document.getElementById('showRSI').checked;
        const hasMACD = document.getElementById('showMACD').checked;
        
        // Calculate focused Y-axis range for better candlestick visibility
        const highs = this.currentData.data.map(item => item.high);
        const lows = this.currentData.data.map(item => item.low);
        const minPrice = Math.min(...lows);
        const maxPrice = Math.max(...highs);
        const priceRange = maxPrice - minPrice;
        
        // Add 10% padding on top and bottom for better visibility
        const padding = priceRange * 0.1;
        const yAxisMin = minPrice - padding;
        const yAxisMax = maxPrice + padding;
        
        // Calculate domains dynamically based on selected indicators
        const subplotHeight = 0.2;  // Height for each indicator subplot
        const volumeHeight = 0.15;  // Height for volume subplot
        const spacing = 0.02;       // Space between subplots
        
        let currentBottom = 0;
        let domains = {};
        
        // Start from bottom and work up
        if (hasMACD) {
            domains.macd = [currentBottom, currentBottom + subplotHeight];
            currentBottom += subplotHeight + spacing;
        }
        
        if (hasRSI) {
            domains.rsi = [currentBottom, currentBottom + subplotHeight];
            currentBottom += subplotHeight + spacing;
        }
        
        // Volume subplot
        domains.volume = [currentBottom, currentBottom + volumeHeight];
        currentBottom += volumeHeight + spacing;
        
        // Price chart takes remaining space
        domains.price = [currentBottom, 1.0];
        
        const layout = {
            title: { 
                text: `${symbol} Price Chart`, 
                font: { color: '#ffffff', size: 14 },
                x: 0.5
            },
            plot_bgcolor: '#1a2332',
            paper_bgcolor: '#1a2332',
            font: { color: '#b3c5d7', size: 11 },
            xaxis: {
                type: 'date',
                rangeslider: { visible: false },  // Remove the slider
                gridcolor: '#3a4553',
                tickfont: { color: '#b3c5d7', size: 10 },
                showgrid: true,
                title: { text: 'Date', font: { size: 11 } },
                // Add padding and enable scrolling
                autorange: false,
                range: this.getXAxisRange()  // Custom range with padding
            },
            yaxis: {
                title: { text: 'Price (₹)', font: { size: 11 } },
                gridcolor: '#3a4553',
                tickfont: { color: '#b3c5d7', size: 10 },
                showgrid: true,
                tickformat: '₹,.0f',
                side: 'right',
                domain: domains.price,
                range: [yAxisMin, yAxisMax]  // Focus on actual price range
            },
            yaxis2: {
                title: { text: '', font: { size: 11 } },  // No title for volume
                gridcolor: '#3a4553',
                tickfont: { color: '#b3c5d7', size: 8 },
                showgrid: false,
                side: 'right',
                domain: domains.volume,
                showticklabels: false  // Hide volume numbers on y-axis
            },
            margin: { l: 10, r: 80, t: 40, b: 80 },
            showlegend: true,
            legend: {
                x: 0,
                y: 1.02,
                bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#b3c5d7', size: 10 },
                orientation: 'h'
            },
            hovermode: 'x unified',
            height: 580
        };

        // Add RSI subplot if selected
        if (hasRSI) {
            layout.yaxis3 = {
                title: { text: 'RSI', font: { color: '#e91e63', size: 10 } },
                tickfont: { color: '#e91e63', size: 10 },
                side: 'left',
                overlaying: false,
                domain: domains.rsi,
                range: [0, 100],
                gridcolor: '#3a4553',
                showgrid: true,
                fixedrange: true  // Prevent zooming on this subplot
            };
        }

        // Add MACD subplot if selected
        if (hasMACD) {
            const macdAxisNumber = hasRSI ? 'yaxis4' : 'yaxis3';
            layout[macdAxisNumber] = {
                title: { text: 'MACD', font: { color: '#2196f3', size: 10 } },
                tickfont: { color: '#2196f3', size: 10 },
                side: 'left',
                overlaying: false,
                domain: domains.macd,
                gridcolor: '#3a4553',
                showgrid: true,
                fixedrange: true,  // Prevent zooming on this subplot
                zeroline: true,
                zerolinecolor: '#666666'  // Add zero line for MACD
            };
        }

        return layout;
    }

    getCurrentSymbol() {
        return document.getElementById('stockSymbol').value.trim().toUpperCase() || 'STOCK';
    }

    getXAxisRange() {
        if (!this.currentData || !this.currentData.data || this.currentData.data.length === 0) {
            return null;  // Let Plotly auto-range
        }
        
        const dates = this.currentData.data.map(item => new Date(item.timestamp));
        const minDate = new Date(Math.min(...dates));
        const maxDate = new Date(Math.max(...dates));
        
        // Add 5% padding on both sides
        const dateRange = maxDate.getTime() - minDate.getTime();
        const padding = dateRange * 0.05;
        
        const paddedMinDate = new Date(minDate.getTime() - padding);
        const paddedMaxDate = new Date(maxDate.getTime() + padding);
        
        return [paddedMinDate, paddedMaxDate];
    }

    updateChartTitle(symbol, data) {
        const titleElement = document.getElementById('chartTitle');
        const currentPriceElement = document.getElementById('currentPrice');
        const priceChangeElement = document.getElementById('priceChange');

        titleElement.textContent = `${symbol} - ${document.getElementById('timeframe').selectedOptions[0].text}`;

        if (data && data.data && data.data.length > 0) {
            const latest = data.data[data.data.length - 1];
            const previous = data.data.length > 1 ? data.data[data.data.length - 2] : latest;
            
            console.log('Latest price data:', latest);
            
            currentPriceElement.textContent = `₹${latest.close.toFixed(2)}`;
            
            const change = latest.close - previous.close;
            const changePercent = (change / previous.close) * 100;
            
            priceChangeElement.textContent = `${change > 0 ? '+' : ''}${change.toFixed(2)} (${changePercent.toFixed(2)}%)`;
            priceChangeElement.className = `change ${change > 0 ? 'positive' : change < 0 ? 'negative' : ''}`;
            
            console.log('Price info updated:', {
                current: latest.close,
                change: change,
                changePercent: changePercent
            });
        }
    }

    updateAnalysis(analysisData, symbol) {
        const summaryElement = document.getElementById('analysisSummary');
        const indicatorsGrid = document.getElementById('indicatorsGrid');
        const indicatorList = document.getElementById('indicatorList');

        // Clear existing content
        indicatorsGrid.innerHTML = '';
        indicatorList.innerHTML = '';
        
        console.log('Technical analysis data received:', analysisData);
        
        if (!analysisData || !analysisData.timeframe_results || analysisData.timeframe_results.length === 0) {
            summaryElement.innerHTML = '<p>Technical analysis data not available</p>';
            return;
        }

        // Get the first timeframe result (usually the one requested)
        const timeframeData = analysisData.timeframe_results[0];
        
        console.log('Processing timeframe data:', timeframeData);
        
        if (timeframeData.error) {
            summaryElement.innerHTML = `<p>Analysis error: ${timeframeData.error}</p>`;
            return;
        }

        if (!timeframeData.indicators) {
            summaryElement.innerHTML = '<p>No technical indicators available</p>';
            return;
        }

        // Update summary using the overall summary from API
        const summary = this.generateAnalysisSummary(analysisData);
        summaryElement.innerHTML = summary;

        // Update indicators in sidebar
        this.updateSidebarIndicators(timeframeData.indicators, indicatorList);

        // Update indicators grid
        this.updateIndicatorsGrid(timeframeData.indicators, indicatorsGrid);
    }

    generateAnalysisSummary(data) {
        if (!data.summary || !data.timeframe_results || data.timeframe_results.length === 0) {
            return '<p>No technical indicators available</p>';
        }

        const summary = data.summary.overall_signals;
        const timeframeData = data.timeframe_results[0];
        const indicators = timeframeData.indicators;
        
        // Count actual signals from indicators
        let bullishCount = 0;
        let bearishCount = 0;
        let neutralCount = 0;
        let totalSignals = 0;

        Object.keys(indicators).forEach(key => {
            const indicator = indicators[key];
            if (indicator && indicator.signal) {
                totalSignals++;
                if (indicator.signal === 'BULLISH') {
                    bullishCount++;
                } else if (indicator.signal === 'BEARISH') {
                    bearishCount++;
                } else {
                    neutralCount++;
                }
            }
        });

        let overallSentiment = 'NEUTRAL';
        let sentimentClass = 'neutral';
        
        if (summary.bearish_percentage > summary.bullish_percentage && summary.bearish_percentage > summary.neutral_percentage) {
            overallSentiment = 'BEARISH';
            sentimentClass = 'bearish';
        } else if (summary.bullish_percentage > summary.bearish_percentage && summary.bullish_percentage > summary.neutral_percentage) {
            overallSentiment = 'BULLISH';
            sentimentClass = 'bullish';
        }


        return `
            <div class="sentiment-summary">
                <div class="overall-sentiment ${sentimentClass}">
                    <strong>Overall Sentiment: ${overallSentiment}</strong>
                </div>
                <div class="signal-breakdown">
                    <div class="signal-item bullish">Bullish: ${summary.bullish_percentage.toFixed(1)}% (${bullishCount} signals)</div>
                    <div class="signal-item bearish">Bearish: ${summary.bearish_percentage.toFixed(1)}% (${bearishCount} signals)</div>
                    <div class="signal-item neutral">Neutral: ${summary.neutral_percentage.toFixed(1)}% (${neutralCount} signals)</div>
                </div>
                <div class="indicators-calculated">
                    <small>Indicators: ${data.summary.indicators_calculated.join(', ')}</small>
                </div>
            </div>
        `;
    }

    updateSidebarIndicators(indicators, container) {
        if (!indicators) return;

        console.log('Updating sidebar indicators:', indicators);
        const indicatorItems = [];

        Object.keys(indicators).forEach(key => {
            const indicator = indicators[key];
            if (indicator && typeof indicator === 'object') {
                const displayName = this.formatIndicatorName(key);
                let value = indicator.current_value || indicator.current || indicator.value || '--';
                let signal = indicator.signal || 'NEUTRAL';
                
                if (typeof value === 'number') {
                    value = value.toFixed(2);
                }

                indicatorItems.push(`
                    <div class="indicator-item">
                        <span>${displayName}</span>
                        <span class="indicator-value ${signal.toLowerCase()}">${value}</span>
                    </div>
                `);
            }
        });

        container.innerHTML = indicatorItems.join('');
    }

    updateIndicatorsGrid(indicators, container) {
        if (!indicators) return;

        console.log('Updating indicators grid:', indicators);
        const cards = [];

        // Key indicators to highlight
        const keyIndicators = ['RSI', 'MACD', 'MA_20', 'EMA_20', 'BollingerBands', 'VWAP'];
        
        keyIndicators.forEach(key => {
            const indicator = indicators[key];
            if (indicator && typeof indicator === 'object') {
                let value = indicator.current_value || indicator.current || indicator.value || '--';
                let signal = indicator.signal || 'NEUTRAL';
                
                // Handle special cases
                if (key === 'MACD' && indicator.current_macd) {
                    value = indicator.current_macd.toFixed(2);
                } else if (key === 'BollingerBands' && indicator.current_middle) {
                    value = indicator.current_middle.toFixed(2);
                }
                
                if (typeof value === 'number') {
                    value = value.toFixed(2);
                }

                const explanation = this.getIndicatorExplanation(key);

                cards.push(`
                    <div class="indicator-card">
                        <div class="indicator-header">
                            <span class="indicator-title">${this.formatIndicatorName(key)}</span>
                            <div class="info-icon">
                                i
                                <div class="info-tooltip">${explanation}</div>
                            </div>
                        </div>
                        <div class="value ${signal.toLowerCase()}">${value}</div>
                    </div>
                `);
            }
        });

        container.innerHTML = cards.join('');
    }

    formatIndicatorName(key) {
        const nameMap = {
            'RSI': 'RSI',
            'MACD': 'MACD',
            'MA_20': 'SMA(20)',
            'MA_50': 'SMA(50)',
            'EMA_20': 'EMA(20)',
            'EMA_50': 'EMA(50)',
            'BollingerBands': 'Bollinger Bands',
            'VWAP': 'VWAP',
            'ATR': 'ATR',
            'Volume_SMA': 'Vol SMA'
        };
        
        return nameMap[key] || key.replace(/_/g, ' ').toUpperCase();
    }

    getIndicatorExplanation(key) {
        const explanations = {
            'RSI': 'Relative Strength Index (0-100): Measures momentum to identify overbought (>70) and oversold (<30) conditions. Values above 70 suggest potential selling opportunities, below 30 suggest buying opportunities.',
            'MACD': 'Moving Average Convergence Divergence: Shows the relationship between two moving averages. When MACD line crosses above signal line, it suggests bullish momentum. When below, bearish momentum.',
            'MA_20': 'Simple Moving Average (20 periods): Average price over the last 20 periods. When price is above SMA(20), it suggests upward trend. Below suggests downward trend.',
            'EMA_20': 'Exponential Moving Average (20 periods): Gives more weight to recent prices than SMA. Reacts faster to price changes. Above EMA suggests uptrend, below suggests downtrend.',
            'BollingerBands': 'Bollinger Bands: Uses middle line (SMA) with upper and lower bands at 2 standard deviations. Price touching upper band may indicate overbought, touching lower band may indicate oversold.',
            'VWAP': 'Volume Weighted Average Price: Average price weighted by volume. Often used as benchmark - price above VWAP suggests bullish sentiment, below suggests bearish sentiment.'
        };
        
        return explanations[key] || 'Technical indicator used for market analysis.';
    }

    async chatWithAI() {
        if (!this.currentData || !this.currentAnalysisData) {
            alert('Please load stock data first');
            return;
        }

        this.showLoading(true);

        try {
            // Prepare all data to send to AI
            const aiRequestData = {
                historical_data: this.currentData,
                technical_analysis: this.currentAnalysisData,
                stock_symbol: this.getCurrentSymbol(),
                timeframe: document.getElementById('timeframe').value,
                days: parseInt(document.getElementById('days').value),
                market_indicators: this.currentMarketIndicators || null
            };

            console.log('Sending data to AI analysis endpoint:', aiRequestData);

            const response = await fetch(`${this.apiBaseUrl}/gemini-ai/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(aiRequestData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to get AI analysis');
            }

            const aiResponse = await response.json();
            
            if (aiResponse.status === 'success') {
                this.showAIAnalysisModal(aiResponse.response_text);
            } else {
                throw new Error(aiResponse.response_text || 'AI analysis failed');
            }

        } catch (error) {
            console.error('Error getting AI analysis:', error);
            alert(`Error getting AI analysis: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    showAIAnalysisModal(analysisText) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('aiAnalysisModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'aiAnalysisModal';
            modal.className = 'ai-modal';
            modal.innerHTML = `
                <div class="ai-modal-content">
                    <div class="ai-modal-header">
                        <h3><span class="ai-icon">🤖</span> AI Analysis</h3>
                        <button class="ai-modal-close" onclick="this.closest('.ai-modal').style.display='none'">&times;</button>
                    </div>
                    <div class="ai-modal-body" id="aiAnalysisContent"></div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        // Update content and show modal
        document.getElementById('aiAnalysisContent').innerHTML = this.formatAIResponse(analysisText);
        modal.style.display = 'flex';

        // Close modal when clicking outside
        modal.onclick = function(e) {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        };
    }

    formatAIResponse(responseText) {
        if (!responseText) return '';
        
        // Convert line breaks to HTML breaks and handle bullet points
        let formatted = responseText
            // Convert \n to <br> for line breaks
            .replace(/\n/g, '<br>')
            // Handle markdown-style bullet points
            .replace(/^\* (.+)/gm, '<li>$1</li>')
            .replace(/^- (.+)/gm, '<li>$1</li>')
            // Handle numbered lists
            .replace(/^\d+\. (.+)/gm, '<li>$1</li>')
            // Handle bold text with **text** or __text__
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/__(.*?)__/g, '<strong>$1</strong>')
            // Handle italic text with *text* or _text_
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            .replace(/_([^_]+)_/g, '<em>$1</em>');

        // Wrap consecutive list items in ul tags
        formatted = formatted.replace(/(<li>.*?<\/li>)(\s*<br>\s*<li>.*?<\/li>)*/g, function(match) {
            // Remove <br> tags between list items and wrap in <ul>
            const cleanMatch = match.replace(/<br>\s*/g, '');
            return `<ul>${cleanMatch}</ul>`;
        });

        // Clean up extra line breaks
        formatted = formatted.replace(/<br>\s*<br>/g, '<br>');

        return formatted;
    }


    // Login Modal Methods
    showLoginModal() {
        console.log('Showing login modal');
        document.getElementById('loginModal').classList.add('show');
        this.resetLoginModal();
    }

    hideLoginModal() {
        document.getElementById('loginModal').classList.remove('show');
    }

    resetLoginModal() {
        // Hide all steps
        document.getElementById('step1').style.display = 'block';
        document.getElementById('step2').style.display = 'none';
        document.getElementById('step3').style.display = 'none';
        document.getElementById('step4').style.display = 'none';
        document.getElementById('stepError').style.display = 'none';
        
        // Clear input
        document.getElementById('requestToken').value = '';
        this.loginUrl = null;
    }

    async getLoginUrl() {
        console.log('Getting login URL...');
        try {
            this.showLoading(true);
            
            console.log('Fetching from:', `${this.apiBaseUrl}/auth/login-url`);
            const response = await fetch(`${this.apiBaseUrl}/auth/login-url`);
            
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error response:', errorData);
                throw new Error(errorData.detail || 'Failed to get login URL');
            }

            const data = await response.json();
            console.log('Login URL response:', data);
            this.loginUrl = data.login_url;
            
            // Move to step 2
            document.getElementById('step1').style.display = 'none';
            document.getElementById('step2').style.display = 'block';
            
        } catch (error) {
            console.error('Error getting login URL:', error);
            this.showLoginError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    openKiteLogin() {
        if (this.loginUrl) {
            // Open in new window/tab
            window.open(this.loginUrl, '_blank');
            
            // Move to step 3
            document.getElementById('step2').style.display = 'none';
            document.getElementById('step3').style.display = 'block';
        } else {
            this.showLoginError('Login URL not available. Please try again.');
        }
    }

    async submitRequestToken() {
        const requestToken = document.getElementById('requestToken').value.trim();
        
        if (!requestToken) {
            alert('Please enter the request token');
            return;
        }

        try {
            this.showLoading(true);
            
            const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ request_token: requestToken })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Authentication failed');
            }

            const data = await response.json();
            
            if (data.status === 'success') {
                // Success - show step 4
                document.getElementById('step3').style.display = 'none';
                document.getElementById('step4').style.display = 'block';
                
                // Update auth status immediately and then close modal
                this.checkBackendStatus();
                setTimeout(() => {
                    this.hideLoginModal();
                }, 2000);
                
            } else {
                throw new Error(data.message || 'Authentication failed');
            }
            
        } catch (error) {
            console.error('Error submitting request token:', error);
            this.showLoginError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    showLoginError(errorMessage) {
        // Hide all steps
        document.getElementById('step1').style.display = 'none';
        document.getElementById('step2').style.display = 'none';
        document.getElementById('step3').style.display = 'none';
        document.getElementById('step4').style.display = 'none';
        
        // Show error
        document.getElementById('stepError').style.display = 'block';
        document.getElementById('errorText').textContent = errorMessage;
    }
    
    // Pattern-related functions
    getSelectedPattern() {
        const patternRadios = document.querySelectorAll('input[name="patternSelect"]');
        for (const radio of patternRadios) {
            if (radio.checked) {
                return radio.value;
            }
        }
        return 'hammer'; // Default to hammer if none selected
    }
    
    addCandlestickPatterns(plotData, dates, patterns, selectedPattern) {
        console.log('Adding candlestick pattern:', selectedPattern);
        
        // Define pattern colors and symbols
        const patternStyles = {
            hammer: { color: '#4CAF50', symbol: '▲', name: 'Hammer' },
            doji: { color: '#FF9800', symbol: '◆', name: 'Doji' },
            marubozu: { color: '#2196F3', symbol: '█', name: 'Marubozu' },
            engulfing: { color: '#9C27B0', symbol: '⬛', name: 'Engulfing' },
            harami: { color: '#F44336', symbol: '◼', name: 'Harami' },
            morning_star: { color: '#00BCD4', symbol: '★', name: 'Morning Star' }
        };
        
        // Only show the selected pattern
        const pattern = patterns[selectedPattern];
        if (pattern && pattern.occurrences && pattern.occurrences.length > 0) {
            const style = patternStyles[selectedPattern];
            if (!style) return;
            
            // Create arrays for pattern markers
            const patternDates = [];
            const patternPrices = [];
            const patternTexts = [];
            const patternColors = [];
            
            pattern.occurrences.forEach(occurrence => {
                const candleIndex = occurrence.candle_index;
                if (candleIndex >= 0 && candleIndex < dates.length) {
                    const date = dates[candleIndex];
                    const high = this.currentData.data[candleIndex].high;
                    
                    patternDates.push(date);
                    patternPrices.push(high * 1.02); // Position slightly above the candle
                    patternTexts.push(`${style.name}<br>Type: ${occurrence.pattern_type}<br>Confidence: ${(occurrence.confidence * 100).toFixed(1)}%<br>${occurrence.description}`);
                    
                    // Color based on pattern type
                    let color = style.color;
                    if (occurrence.pattern_type === 'bullish') {
                        color = '#4CAF50';
                    } else if (occurrence.pattern_type === 'bearish') {
                        color = '#F44336';
                    } else if (occurrence.pattern_type === 'neutral') {
                        color = '#FF9800';
                    }
                    patternColors.push(color);
                }
            });
            
            // Add pattern markers to plot
            if (patternDates.length > 0) {
                plotData.push({
                    type: 'scatter',
                    mode: 'markers+text',
                    x: patternDates,
                    y: patternPrices,
                    text: patternDates.map(() => style.symbol),
                    textposition: 'middle center',
                    textfont: {
                        size: 14,
                        color: patternColors
                    },
                    marker: {
                        size: 8,
                        color: patternColors,
                        symbol: 'circle',
                        line: {
                            width: 2,
                            color: 'white'
                        }
                    },
                    name: `${style.name} (${patternDates.length})`,
                    hovertext: patternTexts,
                    hoverinfo: 'text',
                    yaxis: 'y',
                    showlegend: true,
                    legendgroup: 'patterns'
                });
            }
        }
    }
    
    updatePatternsDisplay(analysisData) {
        const patternsSummary = document.getElementById('patternsSummary');
        
        if (!analysisData || !analysisData.timeframe_results || !analysisData.timeframe_results[0]) {
            patternsSummary.innerHTML = '<p>No pattern data available</p>';
            return;
        }
        
        const patterns = analysisData.timeframe_results[0].candlestick_patterns;
        const summary = analysisData.summary?.candlestick_patterns || {};
        
        if (!patterns || Object.keys(patterns).length === 0) {
            patternsSummary.innerHTML = '<p>No candlestick patterns detected</p>';
            return;
        }
        
        let patternsHtml = '<div class="patterns-grid">';
        
        // Define all patterns in order for consistent display
        const patternOrder = ['hammer', 'doji', 'marubozu', 'engulfing', 'harami', 'morning_star'];
        
        patternOrder.forEach(patternKey => {
            const pattern = patterns[patternKey];
            const patternName = this.formatPatternName(patternKey);
            const patternExplanation = this.getPatternExplanation(patternKey);
            
            let totalCount = 0;
            let bullishCount = 0;
            let bearishCount = 0;
            let neutralCount = 0;
            let lastOccurrence = 'N/A';
            let dominantClass = 'neutral';
            
            if (pattern && pattern.total_count > 0) {
                totalCount = pattern.total_count;
                lastOccurrence = pattern.last_occurrence ? new Date(pattern.last_occurrence).toLocaleDateString() : 'N/A';
                
                // Count by type
                pattern.occurrences.forEach(occurrence => {
                    if (occurrence.pattern_type === 'bullish') bullishCount++;
                    else if (occurrence.pattern_type === 'bearish') bearishCount++;
                    else neutralCount++;
                });
                
                // Determine dominant type
                if (bullishCount > bearishCount && bullishCount > neutralCount) {
                    dominantClass = 'bullish';
                } else if (bearishCount > bullishCount && bearishCount > neutralCount) {
                    dominantClass = 'bearish';
                }
            }
            
            patternsHtml += `
                <div class="pattern-card ${dominantClass}">
                    <div class="pattern-header">
                        <span class="pattern-name">${patternName}</span>
                        <div class="pattern-info">
                            <div class="info-icon">
                                i
                                <div class="info-tooltip">${patternExplanation}</div>
                            </div>
                            <span class="pattern-count">${totalCount}</span>
                        </div>
                    </div>
                    <div class="pattern-breakdown">
                        <div class="pattern-type-count bullish">Bull: ${bullishCount}</div>
                        <div class="pattern-type-count bearish">Bear: ${bearishCount}</div>
                        <div class="pattern-type-count neutral">Neut: ${neutralCount}</div>
                    </div>
                    <div class="pattern-last">Last: ${lastOccurrence}</div>
                </div>
            `;
        });
        
        patternsHtml += '</div>';
        
        // Add legend
        patternsHtml += `
            <div class="pattern-legend">
                <h4>Pattern Legend:</h4>
                <div class="legend-items">
                    <span class="legend-item"><span class="pattern-symbol bullish">▲</span> Hammer</span>
                    <span class="legend-item"><span class="pattern-symbol neutral">◆</span> Doji</span>
                    <span class="legend-item"><span class="pattern-symbol">█</span> Marubozu</span>
                    <span class="legend-item"><span class="pattern-symbol">⬛</span> Engulfing</span>
                    <span class="legend-item"><span class="pattern-symbol bearish">◼</span> Harami</span>
                    <span class="legend-item"><span class="pattern-symbol">★</span> Morning Star</span>
                </div>
            </div>
        `;
        
        patternsSummary.innerHTML = patternsHtml;
    }
    
    formatPatternName(patternKey) {
        const nameMap = {
            'hammer': 'Hammer',
            'doji': 'Doji',
            'marubozu': 'Marubozu',
            'engulfing': 'Engulfing',
            'harami': 'Harami',
            'morning_star': 'Morning Star'
        };
        return nameMap[patternKey] || patternKey.replace(/_/g, ' ').toUpperCase();
    }
    
    getPatternExplanation(patternKey) {
        const explanations = {
            'hammer': 'Bullish reversal pattern with a small body at the top and a long lower shadow. Indicates potential upward price movement after a downtrend. The long lower shadow shows rejection of lower prices.',
            'doji': 'Indecision pattern where open and close prices are very similar, creating a cross-like shape. Suggests market uncertainty and potential trend reversal, especially at key support/resistance levels.',
            'marubozu': 'Strong directional pattern with little to no shadows, indicating sustained buying (bullish) or selling (bearish) pressure. Shows decisive market sentiment with minimal price rejection.',
            'engulfing': 'Reversal pattern where the current candle completely engulfs the previous candle\'s body. Bullish engulfing suggests upward reversal, bearish engulfing suggests downward reversal.',
            'harami': 'Reversal pattern where a small candle is contained within the body of the previous larger candle. Suggests potential trend reversal and indicates market indecision after strong moves.',
            'morning_star': 'Three-candle bullish reversal pattern consisting of: bearish candle, small-bodied candle (star), and bullish candle. Indicates potential upward price movement after a downtrend.'
        };
        
        return explanations[patternKey] || 'Candlestick pattern used for technical analysis and trend identification.';
    }
    
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    updateMarketIndicators(marketData, stockSymbol) {
        const container = document.getElementById('marketIndicatorsContent');
        
        if (!marketData || !marketData.indicators) {
            container.innerHTML = '<p>Market indicators not available</p>';
            return;
        }

        const indicators = marketData.indicators;
        
        let indicatorsHtml = '<div class="market-indicators-grid">';
        
        // India VIX Card
        if (indicators.india_vix !== null) {
            const vixValue = indicators.india_vix.toFixed(2);
            const vixStatus = this.getVixStatus(indicators.india_vix);
            indicatorsHtml += this.createMarketIndicatorCard(
                '📊 India VIX',
                vixValue,
                vixStatus.class,
                vixStatus.label,
                'Volatility index measuring expected market volatility over next 30 days.',
                this.getVixExplanation()
            );
        }

        // Put/Call Ratio Card
        if (indicators.put_call_ratio !== null || indicators.nifty_pcr !== null) {
            const pcrValue = indicators.nifty_pcr || indicators.put_call_ratio;
            if (pcrValue !== null) {
                const pcrStatus = this.getPcrStatus(pcrValue);
                indicatorsHtml += this.createMarketIndicatorCard(
                    '⚖️ Put/Call Ratio',
                    pcrValue.toFixed(2),
                    pcrStatus.class,
                    pcrStatus.label,
                    'Ratio of put options to call options trading volume.',
                    this.getPcrExplanation()
                );
            }
        } else {
            // Show placeholder for PCR
            indicatorsHtml += this.createMarketIndicatorCard(
                '⚖️ Put/Call Ratio',
                'N/A',
                'neutral',
                'Data Loading',
                'Calculating from options data...',
                this.getPcrExplanation()
            );
        }

        // Market Breadth Card
        if (indicators.market_breadth) {
            const breadth = indicators.market_breadth;
            const breadthStatus = this.getBreadthStatus(breadth.advance_decline_ratio);
            const breadthHtml = this.createMarketBreadthCard(breadth, breadthStatus);
            indicatorsHtml += breadthHtml;
        }

        indicatorsHtml += '</div>';

        // Add data sources
        if (marketData.data_sources && marketData.data_sources.length > 0) {
            indicatorsHtml += `
                <div class="data-sources">
                    <strong>Data Sources:</strong>
                    <div class="data-source-tags">
                        ${marketData.data_sources.map(source => `<span class="data-source-tag">${source}</span>`).join('')}
                    </div>
                </div>
            `;
        }

        container.innerHTML = indicatorsHtml;
    }

    createMarketIndicatorCard(title, value, statusClass, statusLabel, description, explanation) {
        return `
            <div class="market-indicator-card">
                <div class="market-indicator-header">
                    <div class="market-indicator-title">
                        ${title}
                    </div>
                    <div class="market-info-icon">
                        i
                        <div class="market-info-tooltip">${explanation}</div>
                    </div>
                </div>
                <div class="market-indicator-value ${statusClass}">${value}</div>
                <div class="market-indicator-description">${description}</div>
                <span class="market-indicator-status ${statusClass}">${statusLabel}</span>
            </div>
        `;
    }

    createMarketBreadthCard(breadth, status) {
        return `
            <div class="market-indicator-card" style="grid-column: 1 / -1;">
                <div class="market-indicator-header">
                    <div class="market-indicator-title">
                        📈 Market Breadth
                    </div>
                    <div class="market-info-icon">
                        i
                        <div class="market-info-tooltip">${this.getBreadthExplanation()}</div>
                    </div>
                </div>
                <div class="market-breadth-details">
                    <div class="breadth-item">
                        <span class="breadth-label">Advances</span>
                        <div class="breadth-value" style="color: var(--accent-green);">${breadth.advances}</div>
                    </div>
                    <div class="breadth-item">
                        <span class="breadth-label">Declines</span>
                        <div class="breadth-value" style="color: var(--accent-red);">${breadth.declines}</div>
                    </div>
                    <div class="breadth-item">
                        <span class="breadth-label">Unchanged</span>
                        <div class="breadth-value">${breadth.unchanged}</div>
                    </div>
                </div>
                <div class="market-indicator-description">
                    A/D Ratio: ${breadth.advance_decline_ratio.toFixed(2)} | ADL: ${breadth.advance_decline_line.toFixed(0)}
                </div>
                <span class="market-indicator-status ${status.class}">${status.label}</span>
            </div>
        `;
    }

    getVixStatus(vix) {
        if (vix < 15) {
            return { class: 'positive', label: 'Low Volatility' };
        } else if (vix < 25) {
            return { class: 'neutral', label: 'Moderate Volatility' };
        } else {
            return { class: 'negative', label: 'High Volatility' };
        }
    }

    getPcrStatus(pcr) {
        if (pcr < 0.7) {
            return { class: 'negative', label: 'Bearish Sentiment' };
        } else if (pcr < 1.0) {
            return { class: 'neutral', label: 'Neutral Sentiment' };
        } else {
            return { class: 'positive', label: 'Bullish Sentiment' };
        }
    }

    getBreadthStatus(ratio) {
        if (ratio > 1.5) {
            return { class: 'positive', label: 'Strong Breadth' };
        } else if (ratio > 0.8) {
            return { class: 'neutral', label: 'Neutral Breadth' };
        } else {
            return { class: 'negative', label: 'Weak Breadth' };
        }
    }

    getVixExplanation() {
        return `
            <strong>India VIX (Volatility Index)</strong>
            The India VIX measures the market's expectation of volatility over the next 30 days. 
            <br><br>
            • <strong>Below 15:</strong> Low volatility, stable market conditions
            <br>
            • <strong>15-25:</strong> Moderate volatility, normal market fluctuations  
            <br>
            • <strong>Above 25:</strong> High volatility, increased market uncertainty
            <br><br>
            Higher VIX values typically indicate fear in the market, while lower values suggest complacency.
        `;
    }

    getPcrExplanation() {
        return `
            <strong>Put/Call Ratio (PCR)</strong>
            The ratio of put options to call options being traded, indicating market sentiment.
            <br><br>
            • <strong>Below 0.7:</strong> Excessive bullishness, potential market top
            <br>
            • <strong>0.7-1.0:</strong> Balanced sentiment, normal market conditions
            <br>  
            • <strong>Above 1.0:</strong> Bearish sentiment, potential market bottom
            <br><br>
            Contrarian indicator: High PCR can signal buying opportunity, low PCR may signal caution.
        `;
    }

    getBreadthExplanation() {
        return `
            <strong>Market Breadth</strong>
            Measures the participation of stocks in the market movement using advance/decline data.
            <br><br>
            • <strong>Advances:</strong> Stocks that closed higher than previous day
            <br>
            • <strong>Declines:</strong> Stocks that closed lower than previous day  
            <br>
            • <strong>A/D Ratio:</strong> Advances divided by declines (>1 = bullish)
            <br>
            • <strong>ADL:</strong> Cumulative measure of market breadth over time
            <br><br>
            Strong breadth (more advances) confirms uptrend health. Weak breadth may signal trend weakness.
        `;
    }

    updateSupportResistanceDisplay(analysisData, stockSymbol) {
        const container = document.getElementById('supportResistanceContent');
        
        if (!analysisData || !analysisData.timeframe_results || !analysisData.timeframe_results[0]) {
            container.innerHTML = '<p>Support and resistance data not available</p>';
            return;
        }

        const indicators = analysisData.timeframe_results[0].indicators;
        const srData = indicators.SupportResistance;
        
        if (!srData) {
            container.innerHTML = '<p>No support and resistance levels detected</p>';
            return;
        }

        let srHtml = '<div class="support-resistance-grid">';

        // Current price and signal
        if (srData.current_price && srData.price_action_signal) {
            const signalClass = this.getPriceActionSignalClass(srData.price_action_signal);
            srHtml += `
                <div class="sr-current-price-card">
                    <div class="sr-card-header">
                        <span class="sr-title">📍 Current Status</span>
                    </div>
                    <div class="sr-current-price">₹${srData.current_price.toFixed(2)}</div>
                    <div class="sr-price-signal ${signalClass}">
                        ${this.formatPriceActionSignal(srData.price_action_signal)}
                    </div>
                </div>
            `;
        }

        // Nearest support and resistance
        srHtml += '<div class="sr-nearest-levels">';
        
        if (srData.nearest_support) {
            const support = srData.nearest_support;
            srHtml += `
                <div class="sr-level-card support">
                    <div class="sr-card-header">
                        <span class="sr-title">🛡️ Nearest Support</span>
                        <span class="sr-strength">Strength: ${support.strength.toFixed(1)}/10</span>
                    </div>
                    <div class="sr-price support">₹${support.price.toFixed(2)}</div>
                    <div class="sr-details">
                        <div class="sr-detail-item">Distance: ${Math.abs(support.distance_from_current).toFixed(2)}%</div>
                        <div class="sr-detail-item">Touches: ${support.touches}</div>
                        <div class="sr-detail-item">Type: ${support.is_dynamic ? 'Dynamic' : 'Static'}</div>
                    </div>
                </div>
            `;
        }

        if (srData.nearest_resistance) {
            const resistance = srData.nearest_resistance;
            srHtml += `
                <div class="sr-level-card resistance">
                    <div class="sr-card-header">
                        <span class="sr-title">🚧 Nearest Resistance</span>
                        <span class="sr-strength">Strength: ${resistance.strength.toFixed(1)}/10</span>
                    </div>
                    <div class="sr-price resistance">₹${resistance.price.toFixed(2)}</div>
                    <div class="sr-details">
                        <div class="sr-detail-item">Distance: ${Math.abs(resistance.distance_from_current).toFixed(2)}%</div>
                        <div class="sr-detail-item">Touches: ${resistance.touches}</div>
                        <div class="sr-detail-item">Type: ${resistance.is_dynamic ? 'Dynamic' : 'Static'}</div>
                    </div>
                </div>
            `;
        }

        srHtml += '</div>'; // Close nearest levels

        // All support levels
        if (srData.support_levels && srData.support_levels.length > 0) {
            srHtml += `
                <div class="sr-all-levels">
                    <h4>🛡️ All Support Levels</h4>
                    <div class="sr-levels-list">
            `;
            
            srData.support_levels.forEach((level, index) => {
                srHtml += `
                    <div class="sr-level-item support">
                        <span class="sr-level-price">₹${level.price.toFixed(2)}</span>
                        <span class="sr-level-strength">Strength: ${level.strength.toFixed(1)}</span>
                        <span class="sr-level-distance">${Math.abs(level.distance_from_current).toFixed(1)}% away</span>
                        <span class="sr-level-touches">${level.touches} touches</span>
                    </div>
                `;
            });

            srHtml += '</div></div>'; // Close levels list and all levels
        }

        // All resistance levels
        if (srData.resistance_levels && srData.resistance_levels.length > 0) {
            srHtml += `
                <div class="sr-all-levels">
                    <h4>🚧 All Resistance Levels</h4>
                    <div class="sr-levels-list">
            `;
            
            srData.resistance_levels.forEach((level, index) => {
                srHtml += `
                    <div class="sr-level-item resistance">
                        <span class="sr-level-price">₹${level.price.toFixed(2)}</span>
                        <span class="sr-level-strength">Strength: ${level.strength.toFixed(1)}</span>
                        <span class="sr-level-distance">${Math.abs(level.distance_from_current).toFixed(1)}% away</span>
                        <span class="sr-level-touches">${level.touches} touches</span>
                    </div>
                `;
            });

            srHtml += '</div></div>'; // Close levels list and all levels
        }

        // Recent level breaks
        if (srData.key_level_breaks && srData.key_level_breaks.length > 0) {
            srHtml += `
                <div class="sr-recent-breaks">
                    <h4>⚡ Recent Level Breaks</h4>
                    <div class="sr-breaks-list">
            `;
            
            srData.key_level_breaks.forEach(breakInfo => {
                const breakClass = breakInfo.break_type === 'breakout' ? 'bullish' : 'bearish';
                const breakIcon = breakInfo.break_type === 'breakout' ? '📈' : '📉';
                srHtml += `
                    <div class="sr-break-item ${breakClass}">
                        <span class="sr-break-icon">${breakIcon}</span>
                        <div class="sr-break-details">
                            <div class="sr-break-type">${breakInfo.break_type.toUpperCase()}</div>
                            <div class="sr-break-price">₹${breakInfo.level_price.toFixed(2)} → ₹${breakInfo.price_at_break.toFixed(2)}</div>
                            <div class="sr-break-significance">Significance: ${breakInfo.significance.toFixed(1)}/10</div>
                            <div class="sr-break-date">${new Date(breakInfo.timestamp).toLocaleDateString()}</div>
                        </div>
                    </div>
                `;
            });

            srHtml += '</div></div>'; // Close breaks list and recent breaks
        }

        srHtml += '</div>'; // Close main grid

        container.innerHTML = srHtml;
    }

    getPriceActionSignalClass(signal) {
        const classMap = {
            'APPROACHING_SUPPORT': 'neutral',
            'APPROACHING_RESISTANCE': 'neutral', 
            'BREAKOUT': 'bullish',
            'BREAKDOWN': 'bearish',
            'NEUTRAL': 'neutral'
        };
        return classMap[signal] || 'neutral';
    }

    formatPriceActionSignal(signal) {
        const formatMap = {
            'APPROACHING_SUPPORT': '🎯 Approaching Support',
            'APPROACHING_RESISTANCE': '🎯 Approaching Resistance',
            'BREAKOUT': '📈 Breakout',
            'BREAKDOWN': '📉 Breakdown', 
            'NEUTRAL': '➡️ Neutral'
        };
        return formatMap[signal] || signal;
    }
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new TradingDashboard();
});