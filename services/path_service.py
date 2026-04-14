"""Convert K-line OHLCV data into SVG path strings for Skia rendering."""


def _compute_ma(closes: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        result[i] = sum(closes[i - period + 1 : i + 1]) / period
    return result


def _values_to_path(values: list[float | None], width: float, height: float) -> str:
    """Convert a list of values to an SVG path string, normalised to [0, height]."""
    points: list[tuple[float, float]] = []
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return ""

    v_min = min(valid)
    v_max = max(valid)
    v_range = v_max - v_min if v_max != v_min else 1.0

    n = len(values)
    x_step = width / max(n - 1, 1)

    for i, v in enumerate(values):
        if v is None:
            continue
        x = round(i * x_step, 2)
        # Invert Y: high values at top (y=0), low values at bottom (y=height)
        y = round(height - (v - v_min) / v_range * height, 2)
        points.append((x, y))

    if not points:
        return ""

    parts = [f"M{points[0][0]},{points[0][1]}"]
    for x, y in points[1:]:
        parts.append(f"L{x},{y}")
    return " ".join(parts)


def build_kline_paths(
    data: list[dict], width: float = 100, height: float = 48
) -> dict:
    """Build SVG path strings from K-line data.

    Returns:
        {
            "close_path": "M0,24 L0.4,22 ...",
            "ma5_path": "...",
            "ma20_path": "...",
            "is_up": True/False,
            "high": float,
            "low": float,
            "latest_close": float,
        }
    """
    if not data or len(data) < 2:
        return {
            "close_path": "",
            "ma5_path": "",
            "ma20_path": "",
            "is_up": True,
            "high": 0,
            "low": 0,
            "latest_close": 0,
        }

    closes = [d["close"] for d in data]

    close_path = _values_to_path(closes, width, height)
    ma5_path = _values_to_path(_compute_ma(closes, 5), width, height)
    ma20_path = _values_to_path(_compute_ma(closes, 20), width, height)

    return {
        "close_path": close_path,
        "ma5_path": ma5_path,
        "ma20_path": ma20_path,
        "is_up": closes[-1] >= closes[0],
        "high": max(closes),
        "low": min(closes),
        "latest_close": closes[-1],
    }
