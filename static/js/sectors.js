const filterEl = document.getElementById('sector-filter');
const chartEl = document.getElementById('sector-chart');

let onFilterChange = null;

export function initSectors({ onFilter }) {
    onFilterChange = onFilter;
    filterEl.addEventListener('change', () => {
        if (onFilterChange) onFilterChange(filterEl.value);
    });
}

export function populateFilter(sectors) {
    // Keep the "全部族群" option, add the rest
    filterEl.innerHTML = '<option value="">全部族群</option>' +
        sectors.map(s => `<option value="${s}">${s}</option>`).join('');
}

export function renderSectorStats(stats) {
    if (!stats || !stats.length) {
        chartEl.innerHTML = '<div style="color:var(--text-dim);font-size:12px">無資料</div>';
        return;
    }

    const maxCount = Math.max(...stats.map(s => s.count));

    chartEl.innerHTML = stats.map(s => `
        <div class="sector-bar-row" data-sector="${s.sector}">
            <span class="sector-label" title="${s.sector}">${s.sector}</span>
            <div class="sector-bar" style="width: ${Math.max((s.count / maxCount) * 100, 8)}%">
                <span class="sector-count">${s.count}</span>
            </div>
            <span class="sector-avg">+${s.avg_change_pct.toFixed(1)}%</span>
        </div>
    `).join('');

    // Click on sector bar to filter
    chartEl.querySelectorAll('.sector-bar-row').forEach(row => {
        row.addEventListener('click', () => {
            const sector = row.dataset.sector;
            filterEl.value = sector;
            if (onFilterChange) onFilterChange(sector);
        });
    });
}
