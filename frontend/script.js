// Trading Dashboard v2 - Fixed Plotly Integration
class TradingDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.chart = null;
        this.currentData = null;
        this.loginUrl = null;
        this.currentAnalysisData = null;
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
        document.getElementById('showRSI').addEventListener('change', () => this.updateChartIndicators());
        document.getElementById('showMACD').addEventListener('change', () => this.updateChartIndicators());
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

            this.updateChart(historicalData, stockSymbol);
            this.updateAnalysis(analysisData, stockSymbol);
            this.updateChartTitle(stockSymbol, historicalData);
            
            // Store analysis data for indicator overlays
            this.currentAnalysisData = analysisData;

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
            
            // Oscillators (RSI, MACD) - these need subplots
            if (document.getElementById('showRSI').checked && indicators.RSI) {
                this.addRSI(plotData, dates, indicators.RSI);
            }
            
            if (document.getElementById('showMACD').checked && indicators.MACD) {
                this.addMACD(plotData, dates, indicators.MACD);
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

        // Generate Gemini opinion section if available
        let geminiOpinion = '';
        if (data.gemini_opinion) {
            const uniqueId = `ai-analysis-${Date.now()}`;
            geminiOpinion = `
                <div class="gemini-opinion">
                    <div class="ai-dropdown-header" onclick="window.tradingDashboard.toggleAIAnalysis('${uniqueId}')">
                        <h4><span class="ai-icon">🤖</span> AI Analysis</h4>
                        <span class="dropdown-arrow" id="${uniqueId}-arrow">▼</span>
                    </div>
                    <div class="ai-opinion-content collapsed" id="${uniqueId}">
                        ${this.formatGeminiOpinion(data.gemini_opinion)}
                    </div>
                </div>
            `;
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
                ${geminiOpinion}
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

    formatGeminiOpinion(opinionText) {
        if (!opinionText) return '';
        
        // Convert line breaks to HTML breaks and handle bullet points
        let formatted = opinionText
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

    toggleAIAnalysis(elementId) {
        const content = document.getElementById(elementId);
        const arrow = document.getElementById(`${elementId}-arrow`);
        
        if (!content || !arrow) return;

        if (content.classList.contains('collapsed')) {
            // Expand
            content.classList.remove('collapsed');
            content.classList.add('expanded');
            arrow.textContent = '▲';
            arrow.style.transform = 'rotate(180deg)';
        } else {
            // Collapse
            content.classList.remove('expanded');
            content.classList.add('collapsed');
            arrow.textContent = '▼';
            arrow.style.transform = 'rotate(0deg)';
        }
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
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new TradingDashboard();
});