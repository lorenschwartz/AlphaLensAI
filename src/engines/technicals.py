"""Technicals engine for equity analysis."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.types import Levels, MACross, Technicals, Trend

# ---------------------------------------------------------------------------
# Private helpers (pure functions, no I/O, no side-effects)
# ---------------------------------------------------------------------------


def _sma(values: List[float], period: int) -> Optional[float]:
    """Simple moving average over the last *period* values."""
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def _ema(values: List[float], period: int) -> Optional[float]:
    """Exponential moving average; returns the final EMA value.

    Seeded with the SMA of the first *period* values, then Wilder-smoothed
    over the remainder.
    """
    if len(values) < period:
        return None
    k = 2.0 / (period + 1)
    ema = sum(values[:period]) / period
    for price in values[period:]:
        ema = price * k + ema * (1.0 - k)
    return ema


def _rsi(closes: List[float], period: int = 14) -> Optional[float]:
    """Compute RSI(*period*) from a close-price series (oldest first).

    Uses Wilder smoothing (modified EMA).  Returns ``None`` when there are
    fewer than *period* + 1 data points.
    """
    if len(closes) < period + 1:
        return None
    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(c, 0.0) for c in changes]
    losses = [abs(min(c, 0.0)) for c in changes]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _detect_levels(prices: List[float], window: int = 5) -> Levels:
    """Identify support (local minima) and resistance (local maxima).

    A price at index *i* is a local min/max if it equals the min/max of the
    surrounding window ``prices[i-window : i+window+1]``.
    """
    support: List[float] = []
    resistance: List[float] = []
    for i in range(window, len(prices) - window):
        segment = prices[i - window : i + window + 1]
        p = prices[i]
        if p == min(segment):
            support.append(round(p, 4))
        if p == max(segment):
            resistance.append(round(p, 4))
    return Levels(
        support=sorted(set(support)),
        resistance=sorted(set(resistance)),
    )


def _resolve_ma_cross(ma50: Optional[float], ma200: Optional[float]) -> MACross:
    """Return the MA-cross state from 50-day and 200-day moving averages."""
    if ma50 is None or ma200 is None:
        return "none"
    if ma50 > ma200:
        return "50>200"
    if ma50 < ma200:
        return "50<200"
    return "none"


def _resolve_trend(
    close: float,
    ma20: Optional[float],
    ma50: Optional[float],
    ma200: Optional[float],
) -> Trend:
    """Classify trend from price position relative to moving averages.

    Uses the longest available MA as the reference benchmark.  A price more
    than 2 % above/below the reference is Up/Down; within 2 % is Sideways.
    """
    ref = next((m for m in (ma200, ma50, ma20) if m is not None), None)
    if ref is None or ref == 0:
        return "Sideways"
    pct = (close - ref) / ref
    if pct > 0.02:
        return "Up"
    if pct < -0.02:
        return "Down"
    return "Sideways"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class TechnicalsEngine:
    """Derives technical indicators from price series or pre-computed scalars.

    All computations are deterministic, stateless, and side-effect-free.
    Missing or insufficient data yields ``None`` for optional fields.
    Required fields (``trend``, ``ma_cross``, ``rsi_14``, ``levels``) fall
    back to neutral defaults so a valid ``Technicals`` model is always
    returned when ``data`` is non-empty.
    """

    def analyze(self, data: Optional[Dict[str, Any]]) -> Optional[Technicals]:
        """Analyze technicals data and return a ``Technicals`` model.

        Accepts pre-computed indicators, raw price series, or both.  When a
        pre-computed key is present it takes precedence over derivation.

        Args:
            data: Dict with any subset of the following keys:

                prices / close_prices : List[float] — closes, oldest first
                highs                 : List[float] — daily highs (ATR)
                lows                  : List[float] — daily lows  (ATR)
                rsi_14                : float       — pre-computed RSI
                ma_20 / ma_50 / ma_200: float       — pre-computed MAs
                macd_line             : float       — pre-computed MACD line
                macd_signal           : float       — pre-computed MACD sig
                atr_14                : float       — pre-computed ATR(14)
                support               : List[float] — support price levels
                resistance            : List[float] — resistance price levels
                trend                 : str         — "Up"|"Down"|"Sideways"
                ma_cross              : str         — "50>200"|"50<200"|"none"

        Returns:
            ``Technicals`` on success, ``None`` when ``data`` is falsy.
        """
        if not data:
            return None

        # -- Parse close prices -----------------------------------------------
        closes: List[float] = []
        try:
            raw = data.get("prices") or data.get("close_prices") or []
            closes = [float(x) for x in raw if x is not None]
        except Exception:
            closes = []

        # -- Moving averages --------------------------------------------------
        ma_20: Optional[float] = None
        ma_50: Optional[float] = None
        ma_200: Optional[float] = None
        try:
            ma_20 = float(data["ma_20"]) if "ma_20" in data else _sma(closes, 20)
        except Exception:
            pass
        try:
            ma_50 = float(data["ma_50"]) if "ma_50" in data else _sma(closes, 50)
        except Exception:
            pass
        try:
            ma_200 = float(data["ma_200"]) if "ma_200" in data else _sma(closes, 200)
        except Exception:
            pass

        # -- RSI (neutral default 50.0 when not computable) -------------------
        rsi_14: float = 50.0
        try:
            if "rsi_14" in data:
                rsi_14 = float(data["rsi_14"])
            elif closes:
                computed = _rsi(closes, 14)
                if computed is not None:
                    rsi_14 = computed
        except Exception:
            pass

        # -- MA cross ---------------------------------------------------------
        ma_cross: MACross = "none"
        try:
            if "ma_cross" in data:
                ma_cross = data["ma_cross"]
            else:
                ma_cross = _resolve_ma_cross(ma_50, ma_200)
        except Exception:
            pass

        # -- Trend ------------------------------------------------------------
        trend: Trend = "Sideways"
        try:
            if "trend" in data:
                trend = data["trend"]
            elif closes:
                trend = _resolve_trend(closes[-1], ma_20, ma_50, ma_200)
        except Exception:
            pass

        # -- Support / resistance levels --------------------------------------
        levels = Levels()
        try:
            if "support" in data or "resistance" in data:
                levels = Levels(
                    support=sorted(float(x) for x in data.get("support", [])),
                    resistance=sorted(float(x) for x in data.get("resistance", [])),
                )
            elif len(closes) >= 11:
                levels = _detect_levels(closes)
        except Exception:
            pass

        # -- MACD -------------------------------------------------------------
        macd_line: Optional[float] = None
        macd_signal: Optional[float] = None
        try:
            if "macd_line" in data:
                macd_line = float(data["macd_line"])
            elif len(closes) >= 26:
                ema12 = _ema(closes, 12)
                ema26 = _ema(closes, 26)
                if ema12 is not None and ema26 is not None:
                    macd_line = ema12 - ema26
        except Exception:
            pass
        try:
            if "macd_signal" in data:
                macd_signal = float(data["macd_signal"])
        except Exception:
            pass

        # -- ATR(14) ----------------------------------------------------------
        atr_14: Optional[float] = None
        try:
            if "atr_14" in data:
                atr_14 = float(data["atr_14"])
            else:
                highs: List[float] = [
                    float(x) for x in data.get("highs", []) if x is not None
                ]
                lows: List[float] = [
                    float(x) for x in data.get("lows", []) if x is not None
                ]
                n = min(len(highs), len(lows), len(closes))
                if n >= 15:
                    trs = [
                        max(
                            highs[i] - lows[i],
                            abs(highs[i] - closes[i - 1]),
                            abs(lows[i] - closes[i - 1]),
                        )
                        for i in range(1, n)
                    ]
                    if len(trs) >= 14:
                        atr_14 = sum(trs[-14:]) / 14
        except Exception:
            pass

        return Technicals(
            trend=trend,
            ma_cross=ma_cross,
            rsi_14=rsi_14,
            levels=levels,
            ma_20=ma_20,
            ma_50=ma_50,
            ma_200=ma_200,
            macd_line=macd_line,
            macd_signal=macd_signal,
            atr_14=atr_14,
        )
