import { formatNumber, formatVolume, formatPercent, changeClass, debounce } from './utils.js';

let allData = [];
let filteredData = [];
let selectedIndex = -1;
let pinnedIndex = -1;
let onSelect = null;
let onHover = null;

const tbody = document.getElementById('ranking-body');
const tableWrapper = document.getElementById('table-wrapper');

export function initRanking({ onStockSelect, onStockHover }) {
    onSelect = onStockSelect;
    onHover = onStockHover;

    tbody.addEventListener('click', (e) => {
        const row = e.target.closest('tr');
        if (!row) return;
        const idx = parseInt(row.dataset.index, 10);
        selectRow(idx);
        pinnedIndex = idx;
    });

    const debouncedHover = debounce((idx) => {
        if (pinnedIndex >= 0) return; // Don't hover-switch when pinned
        highlightRow(idx);
        const stock = filteredData[idx];
        if (stock && onHover) onHover(stock);
    }, 120);

    tbody.addEventListener('mouseenter', (e) => {
        const row = e.target.closest('tr');
        if (row) debouncedHover(parseInt(row.dataset.index, 10));
    }, true);

    tbody.addEventListener('mouseleave', () => {
        if (pinnedIndex >= 0) {
            highlightRow(pinnedIndex);
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter') {
            e.preventDefault();
            handleKey(e.key);
        }
    });
}

function handleKey(key) {
    if (!filteredData.length) return;
    if (key === 'ArrowDown') {
        const next = Math.min(selectedIndex + 1, filteredData.length - 1);
        selectRow(next);
        pinnedIndex = next;
    } else if (key === 'ArrowUp') {
        const prev = Math.max(selectedIndex - 1, 0);
        selectRow(prev);
        pinnedIndex = prev;
    }
}

export function renderTable(data) {
    allData = data;
    filteredData = data;
    selectedIndex = -1;
    pinnedIndex = -1;
    _render();
}

export function filterBySector(sector) {
    if (!sector) {
        filteredData = allData;
    } else {
        filteredData = allData.filter(s => s.sector === sector);
    }
    selectedIndex = -1;
    pinnedIndex = -1;
    _render();
}

function _render() {
    if (!filteredData.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text-dim)">無資料</td></tr>';
        return;
    }

    tbody.innerHTML = filteredData.map((s, i) => `
        <tr data-index="${i}" data-code="${s.code}">
            <td class="col-rank">${s.rank}</td>
            <td class="col-code">${s.code}</td>
            <td class="col-name" title="${s.name}">${s.name}</td>
            <td class="col-close">${formatNumber(s.close)}</td>
            <td class="col-change ${changeClass(s.change_pct)}">${formatPercent(s.change_pct)}</td>
            <td class="col-volume">${formatVolume(s.volume)}</td>
            <td class="col-sector">${s.sector || ''}</td>
        </tr>
    `).join('');
}

function selectRow(idx) {
    highlightRow(idx);
    const stock = filteredData[idx];
    if (stock && onSelect) onSelect(stock);
}

function highlightRow(idx) {
    const prev = tbody.querySelector('tr.selected');
    if (prev) prev.classList.remove('selected');
    selectedIndex = idx;
    const row = tbody.querySelector(`tr[data-index="${idx}"]`);
    if (row) {
        row.classList.add('selected');
        row.scrollIntoView({ block: 'nearest' });
    }
}

export function getFilteredData() {
    return filteredData;
}
