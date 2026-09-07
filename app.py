import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# =========================================================
# SUMAN F&O SECTOR HEATMAP SCANNER
# FIRST 5 MINUTE — 9:15 TO 9:20
# =========================================================

st.set_page_config(
    page_title="Suman F&O 9:20 Scanner",
    page_icon="📊",
    layout="wide"
)

st.title("📊 SUMAN F&O 9:20 SECTOR SCANNER")
st.caption(
    "Top Gainer Sector → Top 3 Green Stocks | "
    "Top Loser Sector → Top 3 Red Stocks"
)

# =========================================================
# F&O STOCKS — SECTOR WISE
# =========================================================

FNO_STOCKS_BY_SECTOR = {

    "BANKING": [
        "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK",
        "KOTAKBANK", "INDUSINDBK", "BANKBARODA",
        "PNB", "FEDERALBNK", "IDFCFIRSTB"
    ],

    "FINANCIAL SERVICES": [
        "BAJFINANCE", "BAJAJFINSV", "SHRIRAMFIN",
        "CHOLAFIN", "MUTHOOTFIN", "MANAPPURAM",
        "PFC", "RECLTD", "LICHSGFIN",
        "ABCAPITAL", "JIOFIN"
    ],

    "IT": [
        "TCS", "INFY", "HCLTECH", "WIPRO",
        "TECHM", "LTIM", "MPHASIS",
        "COFORGE", "PERSISTENT", "OFSS"
    ],

    "AUTO": [
        "MARUTI", "M&M", "TATAMOTORS",
        "EICHERMOT", "HEROMOTOCO",
        "BAJAJ-AUTO", "TVSMOTOR",
        "ASHOKLEY", "BOSCHLTD"
    ],

    "PHARMA & HEALTHCARE": [
        "SUNPHARMA", "DRREDDY", "CIPLA",
        "DIVISLAB", "APOLLOHOSP",
        "AUROPHARMA", "LUPIN",
        "TORNTPHARM", "BIOCON",
        "ZYDUSLIFE", "ALKEM"
    ],

    "ENERGY": [
        "RELIANCE", "ONGC", "IOC", "BPCL",
        "HINDPETRO", "GAIL", "NTPC",
        "POWERGRID", "ADANIGREEN",
        "ADANIPOWER", "TATAPOWER"
    ],

    "METALS": [
        "TATASTEEL", "HINDALCO", "JSWSTEEL",
        "HINDZINC", "VEDL", "NMDC",
        "SAIL", "NATIONALUM"
    ],

    "CAPITAL GOODS & INFRA": [
        "LT", "ABB", "SIEMENS",
        "BHEL", "BEL", "HAL",
        "RVNL", "IRCON", "NBCC",
        "POLYCAB", "CGPOWER"
    ],

    "REALTY": [
        "DLF", "GODREJPROP", "LODHA",
        "PRESTIGE", "OBEROIRLTY",
        "PHOENIXLTD"
    ],

    "FMCG": [
        "HINDUNILVR", "ITC", "NESTLEIND",
        "BRITANNIA", "TATACONSUM",
        "DABUR", "GODREJCP",
        "MARICO", "COLPAL"
    ],

    "TELECOM": [
        "BHARTIARTL", "IDEA"
    ],

    "CHEMICALS": [
        "SRF", "PIIND", "DEEPAKNTR",
        "ATUL", "NAVINFLUOR",
        "AARTIIND", "UPL"
    ],

    "DEFENCE": [
        "HAL", "BEL", "BDL",
        "MAZDOCK", "COCHINSHIP",
        "SOLARINDS"
    ],

    "CONSUMER & RETAIL": [
        "TRENT", "KALYANKJIL",
        "DMART", "TITAN"
    ],

    "LOGISTICS & SERVICES": [
        "CONCOR", "DELHIVERY",
        "IRCTC", "INDIGO"
    ],

    "CEMENT": [
        "ULTRACEMCO", "GRASIM",
        "SHREECEM", "AMBUJACEM",
        "ACC", "DALBHARAT"
    ]
}


# =========================================================
# YAHOO SYMBOL
# =========================================================

def yahoo_symbol(symbol):
    return symbol + ".NS"


# =========================================================
# FIRST 5 MINUTE DATA
# =========================================================

@st.cache_data(ttl=60)
def get_first_5m_data(symbol):

    try:

        data = yf.download(
            yahoo_symbol(symbol),
            period="2d",
            interval="5m",
            progress=False,
            auto_adjust=False
        )

        if data is None or data.empty:
            return None

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.dropna()

        if data.empty:
            return None

        # India timezone
        try:
            if data.index.tz is not None:
                data.index = data.index.tz_convert(
                    "Asia/Kolkata"
                )
        except Exception:
            pass

        today = datetime.now().date()

        today_data = data[
            data.index.date == today
        ]

        if today_data.empty:
            return None

        # -------------------------------------------------
        # FIRST 5 MINUTE CANDLE
        # -------------------------------------------------

        first = today_data.iloc[0]

        open_price = float(first["Open"])
        high_price = float(first["High"])
        low_price = float(first["Low"])
        close_price = float(first["Close"])
        volume = float(first["Volume"])

        if open_price <= 0:
            return None

        change_pct = (
            (close_price - open_price)
            / open_price
        ) * 100

        # -------------------------------------------------
        # CANDLE
        # -------------------------------------------------

        if close_price > open_price:
            candle = "GREEN"

        elif close_price < open_price:
            candle = "RED"

        else:
            candle = "DOJI"

        # -------------------------------------------------
        # OPEN = LOW / HIGH
        # -------------------------------------------------

        # Small tolerance for market-data rounding
        tolerance = max(
            0.01,
            open_price * 0.00005
        )

        is_open_low = abs(
            open_price - low_price
        ) <= tolerance

        is_open_high = abs(
            open_price - high_price
        ) <= tolerance

        if is_open_low:
            open_low_high = "OPEN=LOW"

        elif is_open_high:
            open_low_high = "OPEN=HIGH"

        else:
            open_low_high = ""

        return {
            "Symbol": symbol,
            "Open": open_price,
            "High": high_price,
            "Low": low_price,
            "Close": close_price,
            "Volume": volume,
            "Change %": change_pct,
            "Candle": candle,
            "Open=Low": "OPEN=LOW"
                if is_open_low else "",
            "Open=High": "OPEN=HIGH"
                if is_open_high else "",
            "Open Status": open_low_high
        }

    except Exception:
        return None


# =========================================================
# SCAN ALL STOCKS
# =========================================================

def scan_market():

    results = []

    all_stocks = []

    for sector, stocks in FNO_STOCKS_BY_SECTOR.items():

        for stock in stocks:

            all_stocks.append(
                (sector, stock)
            )

    total = len(all_stocks)

    progress = st.progress(0)

    for i, (sector, stock) in enumerate(
        all_stocks
    ):

        result = get_first_5m_data(stock)

        if result is not None:

            result["Sector"] = sector

            results.append(result)

        progress.progress(
            (i + 1) / total
        )

    progress.empty()

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results)


# =========================================================
# SECTOR HEATMAP
# =========================================================

def create_sector_heatmap(df):

    sector_df = (
        df.groupby("Sector")
        .agg(
            Stocks=("Symbol", "count"),
            Avg_Change=("Change %", "mean"),
            Green=("Candle",
                   lambda x:
                   (x == "GREEN").sum()),
            Red=("Candle",
                 lambda x:
                 (x == "RED").sum())
        )
        .reset_index()
    )

    sector_df["Avg Change %"] = (
        sector_df["Avg_Change"]
        .round(2)
    )

    sector_df = sector_df.sort_values(
        "Avg_Change",
        ascending=False
    )

    return sector_df


# =========================================================
# BUY RANKING
# =========================================================

def rank_buy_stocks(df, sector):

    stocks = df[
        (df["Sector"] == sector) &
        (df["Candle"] == "GREEN")
    ].copy()

    if stocks.empty:
        return stocks

    # OPEN=LOW gets highest priority
    stocks["OpenLowPriority"] = np.where(
        stocks["Open=Low"] == "OPEN=LOW",
        1,
        0
    )

    # First priority = OPEN=LOW
    # Second priority = strongest candle
    stocks = stocks.sort_values(
        by=[
            "OpenLowPriority",
            "Change %"
        ],
        ascending=[
            False,
            False
        ]
    )

    stocks = stocks.head(3)

    stocks["Trade"] = "BUY"

    stocks["Priority"] = range(
        1,
        len(stocks) + 1
    )

    return stocks


# =========================================================
# SELL RANKING
# =========================================================

def rank_sell_stocks(df, sector):

    stocks = df[
        (df["Sector"] == sector) &
        (df["Candle"] == "RED")
    ].copy()

    if stocks.empty:
        return stocks

    # OPEN=HIGH gets highest priority
    stocks["OpenHighPriority"] = np.where(
        stocks["Open=High"] == "OPEN=HIGH",
        1,
        0
    )

    # First priority = OPEN=HIGH
    # Second priority = weakest candle
    stocks = stocks.sort_values(
        by=[
            "OpenHighPriority",
            "Change %"
        ],
        ascending=[
            False,
            True
        ]
    )

    stocks = stocks.head(3)

    stocks["Trade"] = "SELL"

    stocks["Priority"] = range(
        1,
        len(stocks) + 1
    )

    return stocks


# =========================================================
# DISPLAY STOCK TABLE
# =========================================================

def display_stock_table(data):

    if data.empty:

        st.warning(
            "कोई qualifying stock नहीं मिला।"
        )

        return

    display = data[
        [
            "Priority",
            "Symbol",
            "Change %",
            "Candle",
            "Open",
            "High",
            "Low",
            "Close",
            "Open Status",
            "Trade"
        ]
    ].copy()

    display["Change %"] = (
        display["Change %"]
        .round(2)
    )

    for col in [
        "Open",
        "High",
        "Low",
        "Close"
    ]:

        display[col] = (
            display[col]
            .round(2)
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# SCAN BUTTON
# =========================================================

st.divider()

scan_button = st.button(
    "🔄 SCAN 9:15–9:20 FIRST 5 MINUTE",
    type="primary",
    use_container_width=True
)


# =========================================================
# MAIN
# =========================================================

if scan_button:

    with st.spinner(
        "F&O stocks scan हो रहे हैं..."
    ):

        df = scan_market()

    if df.empty:

        st.error(
            "आज का 5-minute data उपलब्ध नहीं है।"
        )

    else:

        # =================================================
        # SECTOR HEATMAP
        # =================================================

        sector_df = create_sector_heatmap(df)

        st.subheader(
            "🔥 F&O SECTOR HEATMAP"
        )

        heatmap = sector_df[
            [
                "Sector",
                "Stocks",
                "Avg Change %",
                "Green",
                "Red"
            ]
        ].copy()

        st.dataframe(
            heatmap,
            use_container_width=True,
            hide_index=True
        )

        # =================================================
        # TOP GAINER SECTOR
        # =================================================

        top_gainer_sector = (
            sector_df.iloc[0]["Sector"]
        )

        top_gainer_change = (
            sector_df.iloc[0]["Avg Change %"]
        )

        st.success(
            f"🚀 TOP GAINER SECTOR: "
            f"{top_gainer_sector} "
            f"({top_gainer_change:+.2f}%)"
        )

        # =================================================
        # TOP 3 BUY
        # =================================================

        buy_stocks = rank_buy_stocks(
            df,
            top_gainer_sector
        )

        st.subheader(
            "🟢 TOP 3 BUY CANDIDATES"
        )

        st.caption(
            "Priority: OPEN=LOW → Strongest GREEN candle"
        )

        display_stock_table(
            buy_stocks
        )

        # =================================================
        # TOP LOSER SECTOR
        # =================================================

        top_loser_sector = (
            sector_df.iloc[-1]["Sector"]
        )

        top_loser_change = (
            sector_df.iloc[-1]["Avg Change %"]
        )

        st.error(
            f"🔻 TOP LOSER SECTOR: "
            f"{top_loser_sector} "
            f"({top_loser_change:+.2f}%)"
        )

        # =================================================
        # TOP 3 SELL
        # =================================================

        sell_stocks = rank_sell_stocks(
            df,
            top_loser_sector
        )

        st.subheader(
            "🔴 TOP 3 SELL CANDIDATES"
        )

        st.caption(
            "Priority: OPEN=HIGH → Weakest RED candle"
        )

        display_stock_table(
            sell_stocks
        )

        # =================================================
        # BEST BUY
        # =================================================

        st.divider()

        st.subheader(
            "🎯 FINAL TRADE WATCH"
        )

        if not buy_stocks.empty:

            best_buy = buy_stocks.iloc[0]

            if best_buy["Open=Low"] == "OPEN=LOW":

                st.success(
                    f"🔥 BUY #1: "
                    f"{best_buy['Symbol']} "
                    f"→ OPEN=LOW + GREEN"
                )

            else:

                st.info(
                    f"🟢 BUY #1: "
                    f"{best_buy['Symbol']} "
                    f"→ GREEN"
                )

        if not sell_stocks.empty:

            best_sell = sell_stocks.iloc[0]

            if best_sell["Open=High"] == "OPEN=HIGH":

                st.error(
                    f"🔥 SELL #1: "
                    f"{best_sell['Symbol']} "
                    f"→ OPEN=HIGH + RED"
                )

            else:

                st.warning(
                    f"🔴 SELL #1: "
                    f"{best_sell['Symbol']} "
                    f"→ RED"
                )

        # =================================================
        # STRATEGY SUMMARY
        # =================================================

        st.divider()

        st.info(
            """
            ### 📌 9:20 STRATEGY

            🟢 BUY:
            Top Gainer Sector
            ↓
            First 5-Minute Candle GREEN
            ↓
            Top 3 Stocks
            ↓
            OPEN=LOW को सबसे ज्यादा Priority

            🔴 SELL:
            Top Loser Sector
            ↓
            First 5-Minute Candle RED
            ↓
            Top 3 Stocks
            ↓
            OPEN=HIGH को सबसे ज्यादा Priority

            ⚠️ यह scanner candidate selection के लिए है;
            trade लेने से पहले अपने risk-management rules लागू करें।
            """
        )
