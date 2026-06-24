"""Opening hours volatility scanner tab."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from engine.alerts.webhooks import dispatch_scan_alerts
from engine.data.storage import DataStore
from engine.data.universe import (
    get_preset,
    get_user_watchlist,
    list_presets,
    list_user_watchlists,
    parse_ticker_list,
    save_user_watchlist,
)
from engine.execution.paper_trader import AlpacaPaperTrader
from engine.signals.opening_scanner import scan_universe
from engine.signals.ml_ranker import load_ranker_if_available
from engine.signals.opening_options import enrich_scan_with_options, recommend_from_scan_row
from engine.signals.regime_filter import RegimeFilter


def _universe_options() -> dict[str, str]:
    options = {f"preset:{name}": desc for name, desc in list_presets().items()}
    for name, count in list_user_watchlists().items():
        options[f"user:{name}"] = f"My watchlist ({count} tickers)"
    options["custom"] = "Custom ticker list"
    return options


def render_opening_scanner_tab() -> None:
    """Render the opening volatility scanner UI."""
    st.markdown(
        """
        <div class="scanner-header">
            <h3>Opening Volatility Scanner</h3>
            <p>Rank tickers by gap, premarket volume, opening range expansion, and relative volume at open.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    universe_options = _universe_options()
    default_key = "preset:opening" if "preset:opening" in universe_options else next(iter(universe_options))

    ucol1, ucol2 = st.columns([1, 2])
    with ucol1:
        selected_universe = st.selectbox(
            "Universe",
            options=list(universe_options.keys()),
            format_func=lambda k: universe_options[k],
            index=list(universe_options.keys()).index(default_key),
        )
    with ucol2:
        if selected_universe == "custom":
            default_tickers = ", ".join(get_preset("opening"))
        elif selected_universe.startswith("preset:"):
            default_tickers = ", ".join(get_preset(selected_universe.split(":", 1)[1]))
        else:
            default_tickers = ", ".join(get_user_watchlist(selected_universe.split(":", 1)[1]))

        tickers_raw = st.text_input(
            "Tickers (comma-separated)",
            value=default_tickers,
            disabled=selected_universe != "custom",
        )

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        _render_watchlist_manager(parse_ticker_list(tickers_raw))
    with col2:
        min_score = st.slider("Min score", 0, 80, 20)
    with col3:
        use_regime = st.checkbox("Regime filter", value=True)
    with col4:
        ranker = load_ranker_if_available()
        use_ml_rank = st.checkbox(
            "ML re-rank",
            value=bool(ranker),
            disabled=ranker is None,
            help="Requires a trained model at data/models/opening_ranker.joblib",
        )

    if st.button("Run Opening Scan", type="primary", use_container_width=True):
        if selected_universe == "custom":
            tickers = parse_ticker_list(tickers_raw)
        elif selected_universe.startswith("preset:"):
            tickers = get_preset(selected_universe.split(":", 1)[1])
        else:
            tickers = get_user_watchlist(selected_universe.split(":", 1)[1])
        if not tickers:
            st.warning("Enter at least one ticker.")
            return

        with st.spinner(f"Scanning {len(tickers)} tickers..."):
            regime_filter = RegimeFilter() if use_regime else None
            results = scan_universe(tickers, regime_filter=regime_filter, min_score=min_score)

        if results.empty:
            st.info("No tickers met the minimum score threshold.")
            return

        if use_ml_rank and ranker is not None:
            results = ranker.rank(results)

        st.session_state["opening_scan_results"] = results

        # Persist top signals
        try:
            store = DataStore()
            for _, row in results.head(10).iterrows():
                store.log_signal(
                    row["ticker"],
                    "opening_scan",
                    row.get("opening_score"),
                    row.to_dict(),
                )
        except Exception:
            pass

    if "opening_scan_results" in st.session_state:
        df = st.session_state["opening_scan_results"]
        display_cols = [
            c
            for c in [
                "ticker",
                "opening_score",
                "ml_score",
                "direction",
                "price",
                "gap_pct",
                "premarket_volume_ratio",
                "or_15m_range_pct",
                "relative_volume_open",
                "regime_label",
                "volatility",
            ]
            if c in df.columns
        ]
        st.dataframe(
            _format_scanner_df(df[display_cols]),
            use_container_width=True,
            hide_index=True,
        )

        if len(df) > 0:
            top = df.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Top pick", top["ticker"])
            c2.metric("Score", f"{top['opening_score']:.0f}")
            c3.metric("Gap", f"{top.get('gap_pct', 0):+.2f}%")
            c4.metric("Regime", top.get("regime_label", "—"))

        _render_options_plays_panel(df)
        _render_alert_panel(df)
        _render_paper_trading_panel(df)


def _render_watchlist_manager(current_tickers: list[str]) -> None:
    with st.expander("Save watchlist", expanded=False):
        name = st.text_input("Watchlist name", placeholder="my_momentum")
        if st.button("Save current tickers", disabled=not current_tickers):
            if not name.strip():
                st.warning("Enter a watchlist name.")
            else:
                try:
                    saved = save_user_watchlist(name, current_tickers)
                    st.success(f"Saved {len(saved)} tickers to '{name}'.")
                except Exception as exc:
                    st.error(str(exc))


def _render_alert_panel(results: pd.DataFrame) -> None:
    """Optional Slack/Discord webhook alert for high-scoring hits."""
    with st.expander("Webhook Alerts (Slack / Discord)", expanded=False):
        st.caption(
            "Send an alert when scan hits exceed a score threshold. "
            "Set SLACK_WEBHOOK_URL and/or DISCORD_WEBHOOK_URL in the environment."
        )
        threshold = st.number_input("Alert min score", min_value=0, max_value=100, value=50, step=5)
        dry_run = st.checkbox("Dry run (preview payload only)", value=True)

        if st.button("Send webhook alert", use_container_width=True):
            summary = {
                "scanned_at": pd.Timestamp.now(tz="America/New_York").isoformat(),
                "results": results.to_dict(orient="records"),
            }
            try:
                result = dispatch_scan_alerts(summary, min_alert_score=float(threshold), dry_run=dry_run)
                if result.get("skipped"):
                    st.warning(f"Alert skipped: {result.get('reason', 'unknown')}")
                else:
                    st.success(
                        f"Alert dispatched for {result.get('hit_count', 0)} hit(s) "
                        f"≥ {result.get('threshold', threshold):.0f}"
                    )
                st.json(result)
            except Exception as exc:
                st.error(f"Alert failed: {exc}")


def _render_options_plays_panel(results: pd.DataFrame) -> None:
    """Suggest straddle/strangle plays when opening range is expanded."""
    with st.expander("Options Plays (Straddle / Strangle)", expanded=False):
        st.caption(
            "Volatility play ideas when the 15-minute opening range is wide. "
            "Theoretical Black-Scholes pricing; enable market quotes for Yahoo mids."
        )
        use_market = st.checkbox("Use market option quotes", value=False)

        enriched = enrich_scan_with_options(results, use_market_quotes=use_market)
        plays = enriched[enriched["options_play_type"] != "none"]
        if plays.empty:
            st.info("No tickers with sufficient opening range expansion for an options play.")
            return

        display = plays[
            [
                "ticker",
                "options_play_type",
                "or_15m_range_pct",
                "options_call_strike",
                "options_put_strike",
                "options_est_debit",
                "options_breakeven_up_pct",
                "options_breakeven_down_pct",
                "options_rationale",
            ]
        ].copy()
        display.columns = [
            "Ticker",
            "Play",
            "OR 15m %",
            "Call K",
            "Put K",
            "Est debit",
            "BE up %",
            "BE down %",
            "Rationale",
        ]
        st.dataframe(display, use_container_width=True, hide_index=True)

        top_play = recommend_from_scan_row(
            plays.iloc[0].to_dict(),
            use_market_quotes=use_market,
        )
        if top_play["play_type"] != "none":
            st.markdown(
                f"**Top play:** {top_play['play_type'].upper()} on **{plays.iloc[0]['ticker']}** — "
                f"debit ~${top_play.get('estimated_debit', 0):.2f}, "
                f"breakevens {top_play.get('breakeven_down_pct', 0):+.1f}% / "
                f"{top_play.get('breakeven_up_pct', 0):+.1f}%"
            )


def _render_paper_trading_panel(results: pd.DataFrame) -> None:
    """Optional Alpaca paper execution — requires explicit user confirmation."""
    with st.expander("Paper Trading (Alpaca)", expanded=False):
        st.caption(
            "Submit market orders on your Alpaca paper account for the top ranked "
            "signals. Orders are not placed until you confirm below."
        )

        trader_probe = AlpacaPaperTrader()
        alpaca_ready = trader_probe.configured

        if alpaca_ready:
            st.success("Alpaca credentials detected.")
        else:
            st.info(
                "No Alpaca credentials found — enable dry run to preview orders, "
                "or set ALPACA_API_KEY and ALPACA_SECRET_KEY in your environment."
            )

        c1, c2, c3 = st.columns(3)
        with c1:
            max_orders = st.number_input("Max orders", min_value=1, max_value=5, value=3)
        with c2:
            notional_usd = st.number_input(
                "Notional per trade ($)", min_value=100, max_value=5000, value=500, step=100
            )
        with c3:
            trade_min_score = st.slider("Min score to trade", 0, 100, 50)

        dry_run = st.checkbox(
            "Dry run (simulate orders, do not submit)",
            value=not alpaca_ready,
            disabled=not alpaca_ready,
            help="When Alpaca is not configured, dry run is always used.",
        )
        if not alpaca_ready:
            dry_run = True

        if alpaca_ready and not dry_run:
            try:
                account = trader_probe.get_account()
                positions = trader_probe.get_positions()
                st.metric("Buying power", f"${float(account.get('buying_power', 0)):,.0f}")
                daily_pnl = trader_probe.guardrails.daily_pnl_pct(account)
                if daily_pnl is not None:
                    st.metric("Daily P&L", f"{daily_pnl:+.2f}%")
                st.caption(
                    f"Guardrails: max loss {trader_probe.guardrails.max_daily_loss_pct:.1f}%, "
                    f"max positions {trader_probe.guardrails.max_open_positions}, "
                    f"max notional ${trader_probe.guardrails.max_notional_per_trade:,.0f}, "
                    f"open positions {len(positions)}"
                )
            except Exception as exc:
                st.error(f"Could not load Alpaca account: {exc}")
        else:
            g = trader_probe.guardrails
            st.caption(
                f"Guardrails active: max daily loss {g.max_daily_loss_pct:.1f}%, "
                f"max {g.max_open_positions} positions, "
                f"${g.max_notional_per_trade:,.0f}/trade"
            )

        confirm = st.checkbox(
            "I confirm I want to submit paper market orders for the top ranked signals",
            value=False,
        )

        if st.button(
            "Execute Top Signals",
            type="secondary",
            disabled=not confirm,
            use_container_width=True,
        ):
            trader = AlpacaPaperTrader(dry_run=dry_run)
            signals = results.to_dict(orient="records")
            try:
                with st.spinner("Submitting orders..."):
                    placed = trader.execute_top_signals(
                        signals,
                        max_orders=int(max_orders),
                        notional_usd=float(notional_usd),
                        min_score=float(trade_min_score),
                    )
            except Exception as exc:
                st.error(f"Order submission failed: {exc}")
                return

            if not placed:
                st.warning("No signals met the trade minimum score or notional threshold.")
                return

            accepted = [p for p in placed if p["order"].get("status") == "accepted"]
            blocked = [p for p in placed if p["order"].get("status") == "blocked"]
            st.session_state["opening_paper_orders"] = placed
            mode = "simulated" if dry_run else "submitted"
            if accepted:
                st.success(f"{len(accepted)} order(s) {mode}.")
            if blocked:
                st.warning(f"{len(blocked)} order(s) blocked by guardrails.")

        if "opening_paper_orders" in st.session_state:
            rows = []
            for item in st.session_state["opening_paper_orders"]:
                signal = item["signal"]
                order = item["order"]
                rows.append(
                    {
                        "ticker": signal.get("ticker"),
                        "score": signal.get("opening_score"),
                        "side": order.get("side"),
                        "qty": order.get("qty"),
                        "status": order.get("status"),
                        "reason": order.get("reason"),
                        "order_id": order.get("id"),
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _format_scanner_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "price" in out.columns:
        out["price"] = out["price"].map(lambda x: f"${x:.2f}")
    if "gap_pct" in out.columns:
        out["gap_pct"] = out["gap_pct"].map(lambda x: f"{x:+.2f}%")
    if "opening_score" in out.columns:
        out["opening_score"] = out["opening_score"].map(lambda x: f"{x:.0f}")
    if "ml_score" in out.columns:
        out["ml_score"] = out["ml_score"].map(lambda x: f"{x:.0f}")
    if "volatility" in out.columns:
        out["volatility"] = out["volatility"].map(lambda x: f"{x:.1%}")
    if "premarket_volume_ratio" in out.columns:
        out["premarket_volume_ratio"] = out["premarket_volume_ratio"].map(lambda x: f"{x:.2f}x")
    if "relative_volume_open" in out.columns:
        out["relative_volume_open"] = out["relative_volume_open"].map(lambda x: f"{x:.2f}x")
    if "or_15m_range_pct" in out.columns:
        out["or_15m_range_pct"] = out["or_15m_range_pct"].map(lambda x: f"{x:.2f}%")
    return out
