const BASE = '/api';

async function request(url, options = {}) {
    const resp = await fetch(url, options);
    if (!resp.ok) {
        const text = await resp.text().catch(() => '');
        throw new Error(`HTTP ${resp.status}: ${text}`);
    }
    return resp.json();
}

export async function fetchRanking(date, top = 100) {
    return request(`${BASE}/ranking?date=${date}&top=${top}`);
}

export async function fetchKline(symbol, days = 240, signal) {
    return request(`${BASE}/kline?symbol=${symbol}&days=${days}`, { signal });
}

export async function fetchSectors() {
    return request(`${BASE}/sectors`);
}

export async function fetchSectorStats(date, top = 100) {
    return request(`${BASE}/sector-stats?date=${date}&top=${top}`);
}

export async function triggerPreload(symbols) {
    return request(`${BASE}/kline/preload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbols }),
    });
}

export async function fetchProgress() {
    return request(`${BASE}/kline/progress`);
}
