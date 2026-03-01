"""
src/reporting/reporter.py

Reporter -- converts a Decision into a self-contained HTML report.

The generated HTML uses inline CSS (dark theme matching ui/index.html) so
the file can be opened directly in any browser with no external assets.

Accepted input types
--------------------
Decision  -- serialised immediately
dict      -- validated against Decision schema first
None/{}   -- returns None (no report for missing data)
other     -- returns None (defensive)
"""

from __future__ import annotations

import html
from typing import Any, Optional

from src.types import Decision


def _esc(value: Any) -> str:
    """HTML-escape a value for safe inline insertion."""
    return html.escape(str(value) if value is not None else "")


def _fmt_float(value: Optional[float], precision: int = 2, prefix: str = "") -> str:
    if value is None:
        return "&#8212;"  # em-dash
    return f"{prefix}{value:.{precision}f}"


def _reco_color(reco: str) -> str:
    return {"BUY": "#34d399", "SELL": "#f87171"}.get(reco, "#fbbf24")


def _trend_color(trend: str) -> str:
    return {"Up": "#34d399", "Down": "#f87171"}.get(trend, "#fbbf24")


def _consensus_color(consensus: str) -> str:
    return {"Buy": "#34d399", "Sell": "#f87171"}.get(consensus, "#fbbf24")


_CSS = """
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0f1117;--surface:#1a1d27;--border:#2a2e3e;
  --text:#e2e8f0;--muted:#8892a4;--radius:8px;
}
body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);padding:2rem 1rem 4rem;line-height:1.5}
.container{max-width:960px;margin:0 auto}
h1{font-size:1.6rem;font-weight:800;margin-bottom:.25rem}
.subtitle{color:var(--muted);font-size:.85rem;margin-bottom:2rem}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:1.25rem;margin-bottom:1rem}
h2{font-size:.95rem;font-weight:600;color:#a78bfa;margin-bottom:.9rem}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
.stat-label{font-size:.7rem;color:var(--muted);margin-bottom:.15rem}
.stat-value{font-size:1rem;font-weight:600}
.badge{display:inline-block;font-weight:800;letter-spacing:.5px;padding:.2rem .8rem;border-radius:6px;font-size:1rem}
table{width:100%;border-collapse:collapse;font-size:.85rem}
th{text-align:left;color:var(--muted);font-weight:500;padding:.35rem .5rem;border-bottom:1px solid var(--border)}
td{padding:.45rem .5rem;border-bottom:1px solid rgba(255,255,255,.04)}
tr:last-child td{border-bottom:none}
ul{list-style:none;padding:0}
li{padding:.3rem 0 .3rem 1.1rem;position:relative;font-size:.88rem;border-bottom:1px solid rgba(255,255,255,.04)}
li::before{content:'>';position:absolute;left:0;color:#6c8fff}
li:last-child{border-bottom:none}
.header-row{display:flex;flex-wrap:wrap;gap:1rem 2rem;align-items:center;margin-bottom:1.25rem}
code{font-family:monospace;font-size:.82rem;color:#a78bfa}
</style>
"""


def _build_html(decision: Decision) -> str:
    d = decision

    # --- header stats -------------------------------------------------------
    reco_color = _reco_color(d.recommendation)
    badge = (
        f'<span class="badge" style="background:rgba(0,0,0,.3);'
        f'color:{reco_color};border:1px solid {reco_color}40">'
        f"{_esc(d.recommendation)}</span>"
    )
    ret_sign = "+" if d.expected_total_return_pct >= 0 else ""
    ret_color = "#34d399" if d.expected_total_return_pct >= 0 else "#f87171"

    header_stats = (
        f'<div class="header-row">'
        f"<div><h1>{_esc(d.ticker)}</h1>"
        f'<div class="subtitle">As of {_esc(d.as_of)} &middot; {d.horizon_months}m horizon</div></div>'
        f"{badge}"
        f'<div><div class="stat-label">Target price</div>'
        f'<div class="stat-value">{_fmt_float(d.target_price_12m, prefix="$")}</div></div>'
        f'<div><div class="stat-label">Expected return</div>'
        f'<div class="stat-value" style="color:{ret_color}">'
        f"{ret_sign}{d.expected_total_return_pct:.1f}%</div></div>"
        f'<div><div class="stat-label">Risk</div>'
        f'<div class="stat-value">{_esc(d.risk_rating)}</div></div>'
        f"</div>"
    )

    # --- thesis & risks -------------------------------------------------------
    thesis_li = "".join(f"<li>{_esc(t)}</li>" for t in d.thesis)
    risks_li = "".join(f"<li>{_esc(r)}</li>" for r in d.key_risks)
    thesis_risks = (
        f'<div class="grid2">'
        f"<div><div style='font-size:.72rem;color:var(--muted);font-weight:600;margin-bottom:.4rem'>THESIS</div>"
        f"<ul>{thesis_li}</ul></div>"
        f"<div><div style='font-size:.72rem;color:var(--muted);font-weight:600;margin-bottom:.4rem'>KEY RISKS</div>"
        f"<ul>{risks_li}</ul></div>"
        f"</div>"
    )

    # --- scenarios ------------------------------------------------------------
    scen_rows = ""
    for name, s in d.scenarios.items():
        eps_str = f"{s.eps:.2f}" if s.eps is not None else "&#8212;"
        scen_rows += (
            f"<tr><td style='font-weight:600;text-transform:capitalize'>{_esc(name)}</td>"
            f"<td>{s.prob:.0%}</td>"
            f"<td>{_fmt_float(s.fair_value, prefix='$')}</td>"
            f"<td>{eps_str}</td></tr>"
        )
    scenarios_table = (
        "<table><thead><tr><th>Case</th><th>Prob</th><th>Fair value</th><th>EPS</th></tr></thead>"
        f"<tbody>{scen_rows}</tbody></table>"
    )

    # --- valuation ------------------------------------------------------------
    def _vrow(
        label: str, val: Optional[float], prefix: str = "$", pct: bool = False
    ) -> str:
        if val is None:
            return ""
        formatted = f"{val * 100:.1f}%" if pct else f"{prefix}{val:.2f}"
        return (
            f"<tr><td style='color:var(--muted)'>{_esc(label)}</td>"
            f"<td style='font-weight:600'>{formatted}</td></tr>"
        )

    val_rows = (
        _vrow("Blended", d.valuation.blended)
        + _vrow("DCF", d.valuation.dcf_fair_value)
        + _vrow("Multiples", d.valuation.multiples_fair_value)
        + _vrow("WACC", d.valuation.wacc, pct=True)
        + _vrow("Terminal g", d.valuation.terminal_g, pct=True)
    )
    valuation_table = f"<table><tbody>{val_rows}</tbody></table>"

    # --- technicals -----------------------------------------------------------
    trend_color = _trend_color(d.technicals.trend)
    tech_rows = (
        f"<tr><td style='color:var(--muted)'>Trend</td>"
        f"<td><span style='color:{trend_color};font-weight:600'>{_esc(d.technicals.trend)}</span></td></tr>"
        f"<tr><td style='color:var(--muted)'>MA Cross</td><td>{_esc(d.technicals.ma_cross)}</td></tr>"
        f"<tr><td style='color:var(--muted)'>RSI (14)</td><td>{d.technicals.rsi_14:.1f}</td></tr>"
    )
    for label, val in [
        ("MA 50", d.technicals.ma_50),
        ("MA 200", d.technicals.ma_200),
        ("ATR (14)", d.technicals.atr_14),
    ]:
        if val is not None:
            tech_rows += f"<tr><td style='color:var(--muted)'>{_esc(label)}</td><td>{val:.2f}</td></tr>"
    if d.technicals.levels.support:
        lvls = ", ".join(f"${v:.2f}" for v in d.technicals.levels.support)
        tech_rows += (
            f"<tr><td style='color:var(--muted)'>Support</td><td>{lvls}</td></tr>"
        )
    if d.technicals.levels.resistance:
        lvls = ", ".join(f"${v:.2f}" for v in d.technicals.levels.resistance)
        tech_rows += (
            f"<tr><td style='color:var(--muted)'>Resistance</td><td>{lvls}</td></tr>"
        )
    technicals_table = f"<table><tbody>{tech_rows}</tbody></table>"

    # --- sentiment ------------------------------------------------------------
    cons_color = _consensus_color(d.sentiment.analyst_consensus)
    sent_rows = (
        f"<tr><td style='color:var(--muted)'>Consensus</td>"
        f"<td><span style='color:{cons_color};font-weight:600'>{_esc(d.sentiment.analyst_consensus)}</span></td></tr>"
    )
    for label, val, prefix in [
        ("Avg target", d.sentiment.avg_target, "$"),
        ("Short interest", d.sentiment.short_interest_pct_float, ""),
        ("News sentiment", d.sentiment.news_sentiment_score, ""),
    ]:
        if val is not None:
            suffix = "%" if label == "Short interest" else ""
            sent_rows += (
                f"<tr><td style='color:var(--muted)'>{_esc(label)}</td>"
                f"<td>{prefix}{val:.2f}{suffix}</td></tr>"
            )
    sentiment_table = f"<table><tbody>{sent_rows}</tbody></table>"

    # --- assumptions ----------------------------------------------------------
    assumptions_section = ""
    if d.assumptions:
        rows = "".join(
            f"<tr><td><code>{_esc(k)}</code></td><td>{_esc(v)}</td></tr>"
            for k, v in d.assumptions.items()
        )
        assumptions_section = (
            f'<div class="card"><h2>Engine assumptions</h2>'
            f"<table><thead><tr><th>Key</th><th>Value</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>"
        )

    # --- monitoring -----------------------------------------------------------
    monitoring_section = ""
    if d.monitoring:
        rows = "".join(
            f"<tr><td>{_esc(m.metric)}</td><td>{_esc(m.threshold)}</td><td>{_esc(m.action)}</td></tr>"
            for m in d.monitoring
        )
        monitoring_section = (
            f'<div class="card"><h2>Monitoring rules</h2>'
            f"<table><thead><tr><th>Metric</th><th>Threshold</th><th>Action</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>"
        )

    # --- catalysts ------------------------------------------------------------
    catalysts_section = ""
    if d.catalysts_next_6_12m:
        rows = "".join(
            f"<tr><td>{_esc(c.event)}</td><td>{_esc(c.window)}</td><td>{_esc(c.impact)}</td></tr>"
            for c in d.catalysts_next_6_12m
        )
        catalysts_section = (
            f'<div class="card"><h2>Catalysts (next 6&#8211;12 months)</h2>'
            f"<table><thead><tr><th>Event</th><th>Window</th><th>Impact</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>"
        )

    return (
        "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
        "<meta charset='UTF-8' />\n"
        f"<title>AlphaLensAI — {_esc(d.ticker)}</title>\n"
        f"{_CSS}\n"
        "</head>\n<body>\n<div class='container'>\n"
        f'<div class="card">{header_stats}{thesis_risks}</div>'
        f'<div class="grid2">'
        f'<div class="card"><h2>Scenarios</h2>{scenarios_table}</div>'
        f'<div class="card"><h2>Valuation</h2>{valuation_table}</div>'
        f"</div>"
        f'<div class="grid2">'
        f'<div class="card"><h2>Technicals</h2>{technicals_table}</div>'
        f'<div class="card"><h2>Sentiment</h2>{sentiment_table}</div>'
        f"</div>"
        f"{assumptions_section}"
        f"{monitoring_section}"
        f"{catalysts_section}"
        "\n</div>\n</body>\n</html>"
    )


class Reporter:
    """Converts a Decision into a self-contained HTML report.

    Input may be a :class:`~src.types.Decision` instance, a plain dict
    (validated against the Decision schema), or ``None``.  Returns ``None``
    for any falsy / unrecognisable input.
    """

    def report(self, result: Any) -> Optional[str]:
        """Render *result* as an HTML report string.

        Args:
            result: A :class:`~src.types.Decision`, a plain dict matching
                    the Decision schema, or ``None``.

        Returns:
            Self-contained HTML string, or ``None`` when *result* is falsy
            or cannot be interpreted as a Decision.
        """
        if not result:
            return None

        if isinstance(result, Decision):
            decision = result
        elif isinstance(result, dict):
            try:
                decision = Decision.validate_or_raise(result)
            except Exception:
                return None
        else:
            return None

        return _build_html(decision)
