import { fetchRanking, fetchKline, fetchSectors, fetchSectorStats, triggerPreload, fetchProgress } from './api.js';
import { initRanking, renderTable, filterBySector } from './ranking.js';
import { initChart, updateChart } from './chart.js';
import { initSectors, populateFilter, renderSectorStats } from './sectors.js';
import { todayString, showToast } from './utils.js';

const datePicker = document.getElementById('date-picker');
const topSelect = document.getElementById('top-select');
const loadingEl = document.getElementById('loading-indicator');
const loadingText = document.getElementById('loading-text');
const progressFill = document.getElementById('progress-fill');

let currentAbort = null;

// ── Init ──
async function init() {
    datePicker.value = todayString();
    datePicker.max = todayString();

    initChart();

    initRanking({
        onStockSelect: (stock) => loadKline(stock),
        onStockHover: (stock) => loadKline(stock),
    });

    initSectors({
        onFilter: (sector) => filterBySector(sector),
    });

    datePicker.addEventListener('change', () => loadAll());
    topSelect.addEventListener('change', () => loadAll());

    // Load sectors list
    try {
        const { sectors } = await fetchSectors();
        populateFilter(sectors);
    } catch (e) {
        console.error('Failed to load sectors:', e);
    }

    await loadAll();
}

async function loadAll() {
    const date = datePicker.value;
    const top = parseInt(topSelect.value, 10);

    showLoading('載入排行資料...');

    try {
        const result = await fetchRanking(date, top);
        if (result.message && !result.data.length) {
            renderTable([]);
            renderSectorStats([]);
            updateChart([], result.message || '無資料');
            showToast(result.message);
            hideLoading();
            return;
        }

        renderTable(result.data);

        // Load sector stats
        try {
            const stats = await fetchSectorStats(date, top);
            renderSectorStats(stats.stats);
        } catch (e) {
            console.error('Sector stats error:', e);
        }

        // Auto-select first stock
        if (result.data.length > 0) {
            loadKline(result.data[0]);
        }

        // Trigger preload for K-line data
        startPreload(result.data);

    } catch (e) {
        showToast('載入失敗: ' + e.message);
        console.error(e);
    }

    hideLoading();
}

async function loadKline(stock) {
    if (currentAbort) currentAbort.abort();
    currentAbort = new AbortController();

    const title = `${stock.code} ${stock.name}　${stock.sector || ''}`;

    try {
        const result = await fetchKline(stock.code, 240, currentAbort.signal);
        updateChart(result.data, title);
    } catch (e) {
        if (e.name === 'AbortError') return;
        updateChart([], title + ' — 無歷史資料');
        console.error('Kline error:', e);
    }
}

async function startPreload(stocks) {
    if (!stocks.length) return;

    const symbols = stocks.map(s => ({ code: s.code, market: s.market }));

    try {
        await triggerPreload(symbols);
        showLoading('預載K線資料...');
        pollProgress();
    } catch (e) {
        console.error('Preload error:', e);
    }
}

async function pollProgress() {
    try {
        const p = await fetchProgress();
        const pct = p.total > 0 ? (p.completed / p.total * 100) : 0;
        progressFill.style.width = pct + '%';
        loadingText.textContent = `預載K線 ${p.completed}/${p.total}`;

        if (p.completed < p.total && p.running) {
            setTimeout(pollProgress, 2000);
        } else {
            hideLoading();
            if (p.failed > 0) {
                showToast(`預載完成，${p.failed} 檔失敗`);
            }
        }
    } catch (e) {
        hideLoading();
    }
}

function showLoading(text) {
    loadingText.textContent = text || '載入中...';
    loadingEl.classList.remove('hidden');
}

function hideLoading() {
    loadingEl.classList.add('hidden');
    progressFill.style.width = '0%';
}

// Go
init().catch(e => console.error('Init error:', e));
