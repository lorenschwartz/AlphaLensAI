# Output Contracts

All data exchanged between pipeline modules is defined as Pydantic models in
`src/types.py`. This document is a human-readable reference. For the
authoritative definition always refer to the source file.

---

## Decision  _(top-level output)_

The canonical output produced by `Orchestrator.run()` and consumed by the
Reporter, LLM Agent, and API layer.

```
Decision
├── as_of                   str           ISO date, e.g. "2025-08-11"
├── ticker                  str           Primary listing symbol, e.g. "AAPL"
├── recommendation          Reco          "BUY" | "HOLD" | "SELL"
├── target_price_12m        float         12-month price target
├── expected_total_return_pct float       Projected total return (%)
├── horizon_months          int           Default 12
├── risk_rating             RiskRating    "Low" | "Medium" | "High"
├── thesis                  List[str]     Top 2–5 bull arguments
├── key_risks               List[str]     Top 2–5 risk factors
├── catalysts_next_6_12m    List[Catalyst]
├── valuation               Valuation
├── scenarios               Dict[str, Scenario]   keys: "bull", "base", "bear"
├── technicals              Technicals
├── sentiment               Sentiment
├── citations               List[Citation]
├── assumptions             Dict[str, float|str]   engine inputs used
├── monitoring              List[MonitoringRule]
└── artifacts               Optional[Dict[str, Any]]
```

Helper methods:
- `Decision.validate_or_raise(data: dict)` — Pydantic v1/v2 compatible constructor
- `decision.short_summary()` → `"2025-08-11 | AAPL → BUY @ 240.00 (18.5% / 12m, risk=Medium)"`

---

## Literal type aliases

```python
RiskRating      = Literal["Low", "Medium", "High"]
Reco            = Literal["BUY", "HOLD", "SELL"]
Trend           = Literal["Up", "Down", "Sideways"]
MACross         = Literal["50>200", "50<200", "none"]
AnalystConsensus = Literal["Buy", "Hold", "Sell"]
```

---

## Sub-objects

### Valuation

```
Valuation
├── blended                 float         Required — blended fair value
├── dcf_fair_value          Optional[float]
├── multiples_fair_value    Optional[float]
├── wacc                    Optional[float ≥ 0]
├── terminal_g              Optional[float]
└── peer_multiples_used     List[str]     e.g. ["EV/EBITDA", "P/E"]
```

### Scenario

```
Scenario
├── prob        float ∈ [0, 1]   Probability weight
├── eps         Optional[float]
└── fair_value  float
```

### Technicals

```
Technicals
├── trend       Trend           "Up" | "Down" | "Sideways"
├── ma_cross    MACross         "50>200" | "50<200" | "none"
├── rsi_14      float ∈ [0, 100]
├── levels      Levels
│   ├── support      List[float]   Ascending support levels
│   └── resistance   List[float]   Ascending resistance levels
├── ma_20       Optional[float]
├── ma_50       Optional[float]
├── ma_200      Optional[float]
├── macd_line   Optional[float]
├── macd_signal Optional[float]
└── atr_14      Optional[float]
```

### Sentiment

```
Sentiment
├── analyst_consensus       AnalystConsensus    "Buy" | "Hold" | "Sell"
├── avg_target              Optional[float]
├── short_interest_pct_float Optional[float ≥ 0]
├── insider_net_buy_90d     Optional[float]
├── news_sentiment_score    Optional[float]     normalised −1…+1
├── delta_analyst_upgrades_90d  Optional[int]
└── delta_avg_target_90d    Optional[float]
```

### Catalyst

```
Catalyst
├── event   str
├── window  str     e.g. "Q1–Q2 2026" or "2026-03-15"
└── impact  Literal["Low", "Medium", "High"]   default "Medium"
```

### MonitoringRule

```
MonitoringRule
├── metric      str    e.g. "Revenue growth"
├── threshold   str    e.g. "< 5% YoY"
└── action      str    e.g. "Downgrade to HOLD"
```

### Citation

```
Citation
├── type    Literal["filing", "news", "api"]
├── id      str          e.g. "AAPL-10K-2024"
├── url     Optional[AnyUrl]
└── loc     Optional[str]   section within source, e.g. "MD&A p.12"
```

---

## Engine output types

### FundamentalsSummary

```
FundamentalsSummary
├── revenue_cagr_3y             Optional[float]   3-year revenue CAGR
├── gross_margin_trend_bps_per_year  Optional[float]
├── op_margin_trend_bps_per_year     Optional[float]
├── fcf_stability_score         Optional[float ∈ [0, 1]]
├── net_debt_to_ebitda          Optional[float]
├── current_ratio               Optional[float]
├── roe                         Optional[float]
├── roic                        Optional[float]
└── notes                       Optional[str]
```

### MacroIndustrySummary

```
MacroIndustrySummary
├── rate_regime         Optional[Literal["Rising","Falling","Stable"]]
├── inflation_trend     Optional[Literal["Rising","Falling","Stable"]]
├── fx_headwind_tailwind Optional[Literal["Headwind","Tailwind","Neutral"]]
├── commodity_links     List[str]
├── sector              Optional[str]
└── notes               Optional[str]
```

---

## Orchestrator `assumptions` keys

The Orchestrator injects the following keys into `Decision.assumptions` when
the corresponding engine run succeeds (existing caller values are never
overwritten):

| Key | Source | Description |
|-----|--------|-------------|
| `rev_cagr_3y` | FundamentalsEngine | 3-year revenue CAGR |
| `op_margin_trend_bps_per_year` | FundamentalsEngine | Operating margin trend |
| `fcf_stability_score` | FundamentalsEngine | FCF coefficient-of-variation score |

---

## API request schema

`POST /analyze` and `POST /analyze/html` accept an `AnalyzeRequest`:

```
AnalyzeRequest                     (src/api/schemas.py)
├── ticker                  str            *required*
├── as_of                   str            *required*  ISO date
├── recommendation          "BUY"|"HOLD"|"SELL"  *required*
├── target_price_12m        float          *required*
├── expected_total_return_pct float        *required*
├── risk_rating             "Low"|"Medium"|"High"  *required*
├── thesis                  List[str]      *required*
├── key_risks               List[str]      *required*
├── valuation               ValuationInput *required*
│   └── blended             float          *required*
├── scenarios               Dict[str, ScenarioInput]  *required*
│   └── {prob, fair_value}  each *required*; eps optional
├── fundamentals            Optional[Dict]
├── macro                   Optional[Dict]
├── technicals              Optional[Dict]
├── sentiment               Optional[Dict]
├── horizon_months          int            default 12
├── assumptions             Optional[Dict[str, float|str]]
├── catalysts_next_6_12m    Optional[List[Dict]]
├── citations               Optional[List[Dict]]
├── monitoring              Optional[List[Dict]]
└── artifacts               Optional[Dict]
```

FastAPI automatically returns HTTP 422 with validation detail for any
schema violation.
