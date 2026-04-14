let chart = null;
let candleSeries = null;
let volumeSeries = null;
let ma5Series = null;
let ma20Series = null;
let ma60Series = null;

const container = document.getElementById('chart-container');
const titleEl = document.getElementById('stock-title');
const ohlcvEl = document.getElementById('stock-ohlcv');

export function initChart() {
    chart = LightweightCharts.createChart(container, {
        width: container.clientWidth || 800,
        height: container.clientHeight || 400,
        layout: {
            background: { color: '#0d1117' },
            textColor: '#d1d4dc',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        },
        grid: {
            vertLines: { color: '#1e222d' },
            horzLines: { color: '#1e222d' },
        },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        timeScale: {
            borderColor: '#363a45',
            timeVisible: false,
        },
        rightPriceScale: { borderColor: '#363a45' },
    });

    // Candlestick — red up, green down (Taiwan convention)
    candleSeries = chart.addSeries(LightweightCharts.CandlestickSeries, {
        upColor: '#ff3333',
        downColor: '#00cc00',
        borderUpColor: '#ff3333',
        borderDownColor: '#00cc00',
        wickUpColor: '#ff3333',
        wickDownColor: '#00cc00',
    });

    // Moving averages
    ma5Series = chart.addSeries(LightweightCharts.LineSeries, {
        color: '#ffeb3b',
        lineWidth: 1,
        crosshairMarkerVisible: false,
        lastValueVisible: false,
        priceLineVisible: false,
    });
    ma20Series = chart.addSeries(LightweightCharts.LineSeries, {
        color: '#2196f3',
        lineWidth: 1,
        crosshairMarkerVisible: false,
        lastValueVisible: false,
        priceLineVisible: false,
    });
    ma60Series = chart.addSeries(LightweightCharts.LineSeries, {
        color: '#e040fb',
        lineWidth: 1,
        crosshairMarkerVisible: false,
        lastValueVisible: false,
        priceLineVisible: false,
    });

    // Volume histogram
    volumeSeries = chart.addSeries(LightweightCharts.HistogramSeries, {
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
    });
    volumeSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.82, bottom: 0 },
    });

    // Crosshair tooltip
    chart.subscribeCrosshairMove((param) => {
        if (!param.time || !param.seriesData) {
            ohlcvEl.classList.add('hidden');
            return;
        }
        const candle = param.seriesData.get(candleSeries);
        if (candle) {
            const c = candle.close >= candle.open ? 'var(--red)' : 'var(--green)';
            ohlcvEl.style.color = c;
            ohlcvEl.textContent = `O ${candle.open}  H ${candle.high}  L ${candle.low}  C ${candle.close}`;
            ohlcvEl.classList.remove('hidden');
        }
    });

    // Expose chart for resize
    window.__chart = chart;

    // Responsive resize — delayed to ensure flex layout is settled
    function resizeChart() {
        const w = container.clientWidth;
        const h = container.clientHeight;
        if (w > 0 && h > 0) {
            chart.resize(w, h);
        }
    }
    // Initial resize after layout settles
    requestAnimationFrame(() => {
        resizeChart();
        requestAnimationFrame(resizeChart);
    });
    new ResizeObserver(() => requestAnimationFrame(resizeChart)).observe(container);
    window.addEventListener('resize', resizeChart);
}

export function updateChart(data, title) {
    titleEl.textContent = title || '請選擇股票';

    if (!data || !data.length) {
        candleSeries.setData([]);
        volumeSeries.setData([]);
        ma5Series.setData([]);
        ma20Series.setData([]);
        ma60Series.setData([]);
        ohlcvEl.classList.add('hidden');
        return;
    }

    candleSeries.setData(data);

    // Volume with color
    volumeSeries.setData(data.map(d => ({
        time: d.time,
        value: d.volume,
        color: d.close >= d.open ? '#ff333360' : '#00cc0060',
    })));

    // MAs
    ma5Series.setData(calcMA(data, 5));
    ma20Series.setData(calcMA(data, 20));
    ma60Series.setData(calcMA(data, 60));

    chart.timeScale().fitContent();
}

function calcMA(data, period) {
    const result = [];
    for (let i = period - 1; i < data.length; i++) {
        let sum = 0;
        for (let j = i - period + 1; j <= i; j++) {
            sum += data[j].close;
        }
        result.push({ time: data[i].time, value: parseFloat((sum / period).toFixed(2)) });
    }
    return result;
}
