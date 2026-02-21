import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os
import pytz
from openai import OpenAI

st.set_page_config(page_title="TradePulse Alpha v1.2", page_icon="🚀", layout="wide")
st.title("🚀 TradePulse Alpha v1.2")
st.markdown("**$1,000 Aggressive AI-Infra Engine | Max $500 Loss | Live 9AM Recs + Deep Research**")

# Live ET clock
et_tz = pytz.timezone('US/Eastern')
now_et = datetime.now(et_tz)
next_open_str = "9:30 AM ET"
st.caption(f"**Live Market Time:** {now_et.strftime('%I:%M %p ET - %b %d, %Y')} | Next open: {next_open_str}")

# ─────────────────────────────────────────────
# Sidebar — API Key Input
# ─────────────────────────────────────────────
st.sidebar.header("🔑 xAI API Key")
st.sidebar.markdown(
    "Enter your [xAI API key](https://console.x.ai) below to enable Grok Deep Research. "
    "This is stored only in your browser session and never committed to GitHub."
)

# Try secrets first (for Streamlit Cloud deployment), then fall back to sidebar input
_secret_key = ""
try:
    _secret_key = st.secrets.get("XAI_API_KEY", "")
except Exception:
    pass

if _secret_key:
    api_key = _secret_key
    st.sidebar.success("✅ API key loaded from Streamlit secrets")
else:
    api_key = st.sidebar.text_input(
        "xAI API Key",
        type="password",
        placeholder="xai-...",
        help="Get your key at https://console.x.ai — stored in session only"
    )
    if api_key:
        st.sidebar.success("✅ API key set for this session")
    else:
        st.sidebar.warning("⚠️ Enter your xAI API key to use Deep Research")

# ─────────────────────────────────────────────
# Portfolio
# ─────────────────────────────────────────────
PORTFOLIO_FILE = "tradepulse_portfolio.json"
RECS_FILE = "tradepulse_recommendations.json"

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return {
        "cash": 0.0,
        "positions": {
            "NVDA": {"shares": 1.506, "avg_cost": 185.80},
            "NBIS": {"shares": 2.640, "avg_cost": 98.50},
            "SMCI": {"shares": 6.711, "avg_cost": 29.80},
            "PATH": {"shares": 8.99,  "avg_cost": 10.10},
            "QQQ":  {"shares": 0.333, "avg_cost": 601.30},
            "ARM":  {"shares": 0.0,   "avg_cost": 0.0},
            "AVGO": {"shares": 0.0,   "avg_cost": 0.0}
        },
        "start_date": "2026-02-17",
        "total_invested": 1000.0
    }

def save_portfolio(port):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(port, f, indent=2)

def load_recommendations():
    if os.path.exists(RECS_FILE):
        with open(RECS_FILE, "r") as f:
            return json.load(f)
    return {"generated_at": None, "content": None}

def save_recommendations(content):
    data = {"generated_at": datetime.now(et_tz).strftime("%B %d, %Y %I:%M %p ET"), "content": content}
    with open(RECS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return data

portfolio = load_portfolio()
recs_data = load_recommendations()

# ─────────────────────────────────────────────
# Live Prices
# ─────────────────────────────────────────────
tickers = list(portfolio["positions"].keys())
data = {}
for t in [t for t in tickers if t] + ["^GSPC"]:
    try:
        info = yf.Ticker(t).info
        data[t] = {"price": info.get("currentPrice") or info.get("regularMarketPrice") or 0}
    except Exception:
        data[t] = {"price": 0}

# ─────────────────────────────────────────────
# Portfolio Calc
# ─────────────────────────────────────────────
total_value = portfolio["cash"]
position_values = {}
unrealized_pnl = 0
for ticker, pos in portfolio["positions"].items():
    if pos["shares"] > 0:
        price = data.get(ticker, {}).get("price", 0)
        value = pos["shares"] * price
        pnl = value - (pos["shares"] * pos["avg_cost"])
        position_values[ticker] = {"value": value, "pnl": pnl, "price": price}
        total_value += value
        unrealized_pnl += pnl

# Risk bar
buffer = total_value - 500
risk_percent = max(0, min(100, (1000 - total_value) / 5))
st.progress(risk_percent / 100, text=f"🚨 Distance to $500 Loss Floor: ${buffer:,.0f} buffer")

st.sidebar.metric("Portfolio Value", f"${total_value:,.2f}", f"{((total_value - 1000) / 1000 * 100):+.2f}%")
st.sidebar.metric("Unrealized P&L", f"${unrealized_pnl:,.2f}")

# ─────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Live Dashboard", "9AM Recommendations", "Deep Research"])

# ── Tab 1: Live Dashboard ──
with tab1:
    st.subheader("Holdings")
    df = pd.DataFrame([{
        "Ticker": t,
        "Shares": p["shares"],
        "Avg Cost": p["avg_cost"],
        "Current Price": position_values.get(t, {}).get("price", 0),
        "Value $": position_values.get(t, {}).get("value", 0),
        "P&L $": position_values.get(t, {}).get("pnl", 0)
    } for t, p in portfolio["positions"].items() if p["shares"] > 0])

    if not df.empty:
        st.dataframe(
            df.style.format({"Avg Cost": "${:.2f}", "Current Price": "${:.2f}", "Value $": "${:.2f}", "P&L $": "${:.2f}"}),
            use_container_width=True
        )
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(
                values=[v["value"] for v in position_values.values()],
                names=list(position_values.keys()),
                hole=0.4, title="Portfolio Allocation"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            fig_line = px.line(
                pd.DataFrame({"Day": ["Start", "Now"], "Value": [1000, total_value]}),
                x="Day", y="Value", title="Portfolio Growth", markers=True
            )
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No open positions yet. Record a trade to get started.")

# ── Tab 2: 9AM Recommendations ──
with tab2:
    next_trading_day = now_et.strftime("%A %b %d, %Y")
    st.subheader(f"9AM Recommendations — {next_trading_day}")

    if recs_data["content"]:
        st.success(f"✅ Last updated by Grok Deep Research: {recs_data['generated_at']}")
        st.markdown(recs_data["content"])
    else:
        st.info("💡 No recommendations yet. Go to the **Deep Research** tab and run Grok analysis to auto-populate recommendations here.")

    st.divider()
    st.subheader("Record Your Executed Trades")
    col1, col2 = st.columns(2)
    with col1:
        trade_ticker = st.selectbox("Ticker", list(portfolio["positions"].keys()))
        trade_action = st.radio("Action", ["Buy", "Sell"])
    with col2:
        trade_amount = st.number_input("Dollar Amount $", min_value=10.0, value=100.0)
        trade_price = st.number_input("Exact Fill Price", min_value=0.01, value=100.0)
    if st.button("Record Trade", type="primary"):
        trade_shares = trade_amount / trade_price
        if trade_action == "Buy":
            if trade_ticker not in portfolio["positions"]:
                portfolio["positions"][trade_ticker] = {"shares": 0, "avg_cost": 0}
            old_cost = portfolio["positions"][trade_ticker]["shares"] * portfolio["positions"][trade_ticker]["avg_cost"]
            new_shares = portfolio["positions"][trade_ticker]["shares"] + trade_shares
            portfolio["positions"][trade_ticker]["avg_cost"] = (old_cost + trade_amount) / new_shares
            portfolio["positions"][trade_ticker]["shares"] = new_shares
            portfolio["cash"] -= trade_amount
        else:
            portfolio["positions"][trade_ticker]["shares"] -= trade_shares
            if portfolio["positions"][trade_ticker]["shares"] <= 0:
                del portfolio["positions"][trade_ticker]
            portfolio["cash"] += trade_amount
        save_portfolio(portfolio)
        st.success(f"✅ Recorded {trade_action} ${trade_amount:.2f} of {trade_ticker} @ ${trade_price:.2f}")
        st.rerun()

# ── Tab 3: Deep Research ──
with tab3:
    st.subheader("Deep Research — Powered by Grok (Expert Mode)")
    st.markdown(
        "Runs a full macro + sector + portfolio analysis using **Grok's expert reasoning mode** "
        "and automatically updates the 9AM Recommendations tab with actionable BUY/SELL guidance."
    )

    if not api_key:
        st.warning("⚠️ Please enter your xAI API key in the **sidebar** to enable Deep Research.")
    else:
        if st.button("📊 RUN DEEP RESEARCH (Grok Expert Mode)", type="primary", use_container_width=True):
            with st.spinner("🧠 Grok is analyzing macro, AI capex, sector rotation, and your portfolio..."):
                try:
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://api.x.ai/v1"
                    )

                    positions_summary = ", ".join(
                        [f"{t}: {p['shares']:.3f} shares @ avg ${p['avg_cost']:.2f}"
                         for t, p in portfolio["positions"].items() if p["shares"] > 0]
                    )

                    prompt = f"""You are TradePulse Alpha — an aggressive $1,000 AI-infrastructure trading engine.

Current date: {now_et.strftime('%B %d, %Y %I:%M %p ET')}
Portfolio value: ${total_value:,.2f} (started at $1,000 on Feb 17 2026)
Unrealized P&L: ${unrealized_pnl:,.2f}
Risk floor: $500 (current buffer: ${buffer:,.2f})
Positions: {positions_summary}

Conduct expert-level deep research and produce a structured 9AM trading brief covering:

1. MACRO OUTLOOK — Fed stance, inflation, rates, USD, any overnight news
2. AI CAPEX PULSE — hyperscaler spend updates (Meta, MSFT, Google, Amazon), GPU demand, AI chip supply
3. SECTOR ROTATION — momentum shifts across AI infra, semiconductors, software, broad market (QQQ/SPY)
4. PORTFOLIO REVIEW — assess each current position (NVDA, NBIS, SMCI, PATH, QQQ, ARM, AVGO) with a HOLD/BUY MORE/TRIM/SELL rating and reasoning
5. 9AM ACTION PLAN — exact BUY and SELL recommendations with dollar amounts that fit within the portfolio size and respect the $500 loss floor

Format the output as a clean markdown brief with headers. End with a clearly formatted section:
## 9AM Action Plan
**BUY:**
- TICKER $amount — reason
**SELL/TRIM:**
- TICKER $amount — reason
**HOLD:**
- TICKER — reason

Be disciplined, data-driven, and concise."""

                    response = client.chat.completions.create(
                        model="grok-3-beta",
                        messages=[
                            {"role": "system", "content": "You are an expert quantitative trading analyst with deep knowledge of AI infrastructure stocks, macroeconomics, and portfolio risk management."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=2000
                    )

                    grok_output = response.choices[0].message.content

                    # Save to recommendations file → auto-updates Tab 2
                    saved = save_recommendations(grok_output)

                    # Append to history log
                    with open("deep_research_history.txt", "a") as f:
                        f.write(f"\n\n=== {saved['generated_at']} ===\n{grok_output}")

                    st.success("✅ Grok Deep Research complete — 9AM Recommendations tab updated!")
                    st.markdown(grok_output)

                except Exception as e:
                    st.error(f"❌ API error: {e}")
                    st.info("Double-check your xAI API key in the sidebar and make sure it has credits.")

        # Show last research timestamp
        if recs_data["generated_at"]:
            st.caption(f"Last research run: {recs_data['generated_at']}")

st.caption("TradePulse Alpha v1.2 | Grok Expert Mode | Yahoo Finance | Auto-saves | Secrets-safe")
