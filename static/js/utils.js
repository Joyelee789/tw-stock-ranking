export function formatNumber(n) {
    if (n == null) return '--';
    return n.toLocaleString('zh-TW');
}

export function formatVolume(v) {
    if (v == null) return '--';
    const lots = Math.round(v / 1000);
    if (lots >= 10000) return (lots / 10000).toFixed(1) + '萬';
    return lots.toLocaleString('zh-TW');
}

export function formatPercent(pct) {
    if (pct == null) return '--';
    const sign = pct > 0 ? '+' : '';
    return sign + pct.toFixed(2) + '%';
}

export function changeClass(pct) {
    if (pct > 0) return 'positive';
    if (pct < 0) return 'negative';
    return 'neutral';
}

export function todayString() {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}

export function debounce(fn, ms) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), ms);
    };
}

export function showToast(msg, duration = 3000) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.classList.remove('hidden');
    setTimeout(() => el.classList.add('hidden'), duration);
}
