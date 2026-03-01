"""
src/llm/llm_agent.py

LLM reasoning and gap-filling agent for the AlphaLensAI pipeline.

The agent is backend-agnostic: callers inject any callable that accepts a
prompt string and returns a response string.  When no backend is provided
the agent operates in stub mode (all interact() calls return None), which
is sufficient for deterministic pipeline runs.

Default system prompt is loaded from docs/system_prompt.md at construction
time so prompt content stays in one place.  Pass system_prompt= to override.

Prompt builders
---------------
build_decision_prompt(decision)   -- full analysis context for gap-filling
build_risk_check_prompt(decision) -- focused risk assessment context
"""

from __future__ import annotations

import pathlib
from typing import Any, Callable, Optional

from src.types import Decision

# Path to the docs directory relative to this file's location
_DOCS_DIR = pathlib.Path(__file__).parent.parent.parent / "docs"
_SYSTEM_PROMPT_PATH = _DOCS_DIR / "system_prompt.md"
_RISK_CHECKER_PATH = _DOCS_DIR / "risk_checker_prompt.md"

_FALLBACK_SYSTEM_PROMPT = (
    "You are AlphaLensAI, a modular agentic research pipeline for equity "
    "analysis. Your role is to synthesise fundamental, technical, sentiment, "
    "and macroeconomic analysis into clear, auditable investment decisions."
)

_FALLBACK_RISK_PROMPT = (
    "You are the Risk Checker agent. Review the supplied equity analysis and "
    "enumerate all material risks with likelihood, impact, and monitoring rules."
)


def _load_file(path: pathlib.Path, fallback: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return fallback


class LLMAgent:
    """LLM reasoning and gap-filling agent.

    Args:
        system_prompt: Override the default system prompt loaded from
                       ``docs/system_prompt.md``.
        backend:       Callable ``(prompt: str) -> str`` that calls the
                       LLM of choice.  ``None`` (default) puts the agent
                       in stub mode — ``interact()`` always returns ``None``.
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        backend: Optional[Callable[[str], str]] = None,
    ) -> None:
        self.system_prompt: str = (
            system_prompt
            if system_prompt is not None
            else _load_file(_SYSTEM_PROMPT_PATH, _FALLBACK_SYSTEM_PROMPT)
        )
        self._risk_checker_prompt: str = _load_file(
            _RISK_CHECKER_PATH, _FALLBACK_RISK_PROMPT
        )
        self._backend = backend

    # ------------------------------------------------------------------
    # Core interaction
    # ------------------------------------------------------------------

    def interact(self, prompt: Any) -> Optional[str]:
        """Send *prompt* to the LLM backend and return the response.

        Args:
            prompt: Prompt string.  Returns ``None`` for empty / whitespace
                    prompts or when no backend is configured.

        Returns:
            Backend response string, or ``None`` on any failure / stub mode.
        """
        if not prompt or not str(prompt).strip():
            return None
        if self._backend is None:
            return None
        try:
            return self._backend(str(prompt))
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def build_decision_prompt(self, decision: Decision) -> str:
        """Format *decision* into a structured analysis prompt.

        Includes the system prompt context followed by a structured summary
        of all key Decision fields so the LLM can reason about gaps or
        provide additional narrative.

        Args:
            decision: A populated :class:`~src.types.Decision` instance.

        Returns:
            Formatted multi-line prompt string.
        """
        thesis_bullets = "\n".join(f"  - {t}" for t in decision.thesis)
        risk_bullets = "\n".join(f"  - {r}" for r in decision.key_risks)

        scen_lines = []
        for name, s in decision.scenarios.items():
            eps_str = f", EPS={s.eps:.2f}" if s.eps is not None else ""
            scen_lines.append(
                f"  {name.upper()}: prob={s.prob:.0%}, fair_value=${s.fair_value:.2f}{eps_str}"
            )

        assumptions_lines = (
            "\n".join(f"  {k}: {v}" for k, v in decision.assumptions.items())
            if decision.assumptions
            else "  (none)"
        )

        return (
            f"{self.system_prompt}\n\n"
            "## Equity Analysis — Full Decision Context\n\n"
            f"Ticker:             {decision.ticker}\n"
            f"As of:              {decision.as_of}\n"
            f"Recommendation:     {decision.recommendation}\n"
            f"Target price (12m): ${decision.target_price_12m:.2f}\n"
            f"Expected return:    {decision.expected_total_return_pct:.1f}%\n"
            f"Horizon:            {decision.horizon_months} months\n"
            f"Risk rating:        {decision.risk_rating}\n\n"
            f"### Thesis\n{thesis_bullets}\n\n"
            f"### Key Risks\n{risk_bullets}\n\n"
            f"### Valuation\n"
            f"  Blended:   ${decision.valuation.blended:.2f}\n"
            + (
                f"  DCF:       ${decision.valuation.dcf_fair_value:.2f}\n"
                if decision.valuation.dcf_fair_value is not None
                else ""
            )
            + (
                f"  Multiples: ${decision.valuation.multiples_fair_value:.2f}\n"
                if decision.valuation.multiples_fair_value is not None
                else ""
            )
            + f"\n### Scenarios\n{chr(10).join(scen_lines)}\n\n"
            f"### Technicals\n"
            f"  Trend: {decision.technicals.trend}, "
            f"MA Cross: {decision.technicals.ma_cross}, "
            f"RSI(14): {decision.technicals.rsi_14:.1f}\n\n"
            f"### Sentiment\n"
            f"  Consensus: {decision.sentiment.analyst_consensus}\n\n"
            f"### Assumptions\n{assumptions_lines}\n\n"
            "Please review the above and provide any additional reasoning, "
            "gap-fill missing context, or flag concerns."
        )

    def build_risk_check_prompt(self, decision: Decision) -> str:
        """Format *decision* into a risk-checker prompt.

        Uses the risk_checker_prompt.md context and focuses on risks,
        scenarios, and assumptions that may need deeper scrutiny.

        Args:
            decision: A populated :class:`~src.types.Decision` instance.

        Returns:
            Formatted multi-line risk-checker prompt string.
        """
        risk_bullets = "\n".join(f"  - {r}" for r in decision.key_risks)
        bear = decision.scenarios.get("bear")
        bear_str = f"${bear.fair_value:.2f} (prob={bear.prob:.0%})" if bear else "n/a"

        assumptions_lines = (
            "\n".join(f"  {k}: {v}" for k, v in decision.assumptions.items())
            if decision.assumptions
            else "  (none)"
        )

        return (
            f"{self._risk_checker_prompt}\n\n"
            "## Risk Check Request\n\n"
            f"Ticker:         {decision.ticker}\n"
            f"Recommendation: {decision.recommendation} @ ${decision.target_price_12m:.2f}\n"
            f"Risk rating:    {decision.risk_rating}\n\n"
            f"### Identified Key Risks\n{risk_bullets}\n\n"
            f"### Bear Case\n  {bear_str}\n\n"
            f"### Assumptions in use\n{assumptions_lines}\n\n"
            "Please enumerate all material risks, assess likelihood and impact, "
            "and recommend monitoring rules for each."
        )
