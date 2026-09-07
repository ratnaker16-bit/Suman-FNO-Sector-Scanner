import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, time
from zoneinfo import ZoneInfo


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Suman F&O Multi-Timeframe Scanner",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# TIMEZONE
# ============================================================

IST = ZoneInfo("Asia/Kolkata")

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

PREMARKET_START = time(9, 0)
PREMARKET_END = time(9, 15)

TWO_MIN_END = time(9, 17)
FIVE_MIN_END = time(9, 20)
FIFTEEN_MIN_END = time(9, 30)


# ============================================================
# TITLE
# ============================================================

st.title("📊 Suman F&O Multi-Timeframe Scanner")

st.caption(
    "Pre-Market → 2M → 5M → 15M | "
    "Sector Heatmap | OPEN=LOW / OPEN=HIGH | BUY / SELL"
)


# ============================================================
# F&O STOCK LIST
# ============================================================

FNO_STOCKS_BY_SECTOR = {

    "BANKING": [
        "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK",
        "KOTAKBANK", "INDUSINDBK", "BANKBARODA",
        "PNB", "FEDERALBNK", "IDFCFIRSTB",
        "AUBANK", "CANBK", "INDIANB",
        "BANDHANBNK", "RBLBANK"
    ],

    "FINANCIAL SERVICES": [
        "BAJFINANCE", "BAJAJFINSV", "SHRIRAMFIN",
        "CHOLAFIN", "MUTHOOTFIN", "MANAPPURAM",
        "PFC", "RECLTD", "LICHSGFIN",
        "ABCAPITAL", "JIOFIN", "HUDCO",
        "IREDA", "IRFC"
    ],

    "IT": [
        "TCS", "INFY", "HCLTECH", "WIPRO",
        "TECHM", "LTIM", "MPHASIS",
        "COFORGE", "PERSISTENT", "OFSS"
    ],

    "AUTO": [
        "MARUTI", "M&M", "TATAMOTORS",
        "EICHERMOT", "HEROMOTOCO", "BAJAJ-AUTO",
        "TVSMOTOR", "ASHOKLEY", "BOSCHLTD",
        "MOTHERSON", "EXIDEIND", "ATHERENERG"
    ],

    "PHARMA & HEALTHCARE": [
        "SUNPHARMA", "DRREDDY", "CIPLA",
        "DIVISLAB", "APOLLOHOSP", "AUROPHARMA",
        "LUPIN", "TORNTPHARM", "BIOCON",
        "ZYDUSLIFE", "ALKEM", "GRANULES",
        "GLENMARK", "LAURUSLABS"
    ],

    "ENERGY": [
        "RELIANCE", "ONGC", "IOC", "BPCL",
        "HINDPETRO", "GAIL", "NTPC",
        "POWERGRID", "ADANIGREEN",
        "ADANIPOWER", "TATAPOWER",
        "COALINDIA", "OIL"
    ],

    "METALS": [
        "TATASTEEL", "HINDALCO", "JSWSTEEL",
        "HINDZINC", "VEDL", "NMDC",
        "SAIL", "NATIONALUM", "JINDALSTEL"
    ],

    "CAPITAL GOODS & INFRA": [
        "LT", "ABB", "SIEMENS", "BHEL",
        "RVNL", "IRCON", "NBCC",
        "POLYCAB", "CGPOWER", "CUMMINSIND",
        "KEI"
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
        "DMART", "TITAN",
        "VMM"
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


# ============================================================
# CREATE UNIQUE STOCK -> SECTOR MAPPING
# ============================================================

STOCK_SECTOR = {}

for sector, stocks in FNO_STOCKS_BY_SECTOR.items():
    for stock in stocks:
        if stock not in STOCK_SECTOR:
            STOCK_SECTOR[stock] = sector


ALL_STOCKS = list(STOCK_SECTOR.keys())


# ============================================================
# YAHOO SYMBOL
# ============================================================

def yahoo_symbol(symbol):
    return f"{symbol}.NS"


# ============================================================
# DOWNLOAD DATA IN BATCHES
# ============================================================

@st.cache_data(ttl=20, show_spinner=False)
def download_batch(symbols):

    tickers = [yahoo_symbol(s) for s in symbols]

    try:

        data = yf.download(
            tickers=tickers,
            period="2d",
            interval="1m",
            prepost=True,
            auto_adjust=False,
            progress=False,
            group_by="ticker",
            threads=True
        )

        return data

    except Exception:
        return pd.DataFrame()


# ============================================================
# EXTRACT ONE STOCK FROM BATCH
# ============================================================

def extract_stock_data(raw_data, symbol):

    if raw_data is None or raw_data.empty:
        return None

    ticker = yahoo_symbol(symbol)

    try:

        if isinstance(raw_data.columns, pd.MultiIndex):

            level0 = raw_data.columns.get_level_values(0)
            level1 = raw_data.columns.get_level_values(1)

            if ticker in level0:
                df = raw_data[ticker].copy()

            elif ticker in level1:
                df = raw_data.xs(
                    ticker,
                    axis=1,
                    level=1
                ).copy()

            else:
                return None

        else:

            df = raw_data.copy()

        required = ["Open", "High", "Low", "Close", "Volume"]

        for col in required:
            if col not in df.columns:
                return None

        df = df[required].dropna(
            subset=["Open", "High", "Low", "Close"]
        )

        if df.empty:
            return None

        # Timezone
        if df.index.tz is None:
            df.index = (
                df.index
                .tz_localize("UTC")
                .tz_convert(IST)
            )
        else:
            df.index = df.index.tz_convert(IST)

        return df

    except Exception:
        return None


# ============================================================
# PREVIOUS DAY CLOSE
# ============================================================

def get_previous_close(df, today):

    previous = df[df.index.date < today]

    if previous.empty:
        return np.nan

    # Prefer regular market session
    previous_regular = previous[
        previous.index.time <= MARKET_CLOSE
    ]

    if not previous_regular.empty:
        return float(previous_regular.iloc[-1]["Close"])

    return float(previous.iloc[-1]["Close"])


# ============================================================
# OPEN = LOW / OPEN = HIGH
# ============================================================

def get_open_status(open_price, high_price, low_price):

    if pd.isna(open_price):
        return "N/A"

    tolerance = max(
        0.01,
        abs(open_price) * 0.00005
    )

    if abs(open_price - low_price) <= tolerance:
        return "OPEN=LOW"

    if abs(open_price - high_price) <= tolerance:
        return "OPEN=HIGH"

    return "NORMAL"


# ============================================================
# AGGREGATE FIRST WINDOW
# ============================================================

def aggregate_window(
    regular_df,
    start_time,
    end_time,
    expected_bars
):

    if regular_df is None or regular_df.empty:
        return None

    window = regular_df[
        (regular_df.index.time >= start_time) &
        (regular_df.index.time < end_time)
    ].copy()

    if window.empty:
        return None

    # Window must be complete
    if len(window) < expected_bars:
        return None

    window = window.sort_index()

    open_price = float(window.iloc[0]["Open"])
    high_price = float(window["High"].max())
    low_price = float(window["Low"].min())
    close_price = float(window.iloc[-1]["Close"])

    volume = float(window["Volume"].fillna(0).sum())

    if open_price == 0:
        change_pct = np.nan
    else:
        change_pct = (
            (close_price - open_price)
            / open_price
        ) * 100

    if change_pct > 0:
        candle = "GREEN"
    elif change_pct < 0:
        candle = "RED"
    else:
        candle = "DOJI"

    open_status = get_open_status(
        open_price,
        high_price,
        low_price
    )

    return {
        "Open": open_price,
        "High": high_price,
        "Low": low_price,
        "Close": close_price,
        "Volume": volume,
        "Change %": change_pct,
        "Candle": candle,
        "Open Status": open_status
    }


# ============================================================
# PRE-MARKET ANALYSIS
# ============================================================

def get_premarket_analysis(df, today):

    previous_close = get_previous_close(
        df,
        today
    )

    today_data = df[
        df.index.date == today
    ].copy()

    if today_data.empty:
        return None

    premarket = today_data[
        (today_data.index.time >= PREMARKET_START) &
        (today_data.index.time < PREMARKET_END)
    ].copy()

    if premarket.empty:
        return None

    if pd.isna(previous_close) or previous_close == 0:
        return None

    pre_open = float(premarket.iloc[0]["Open"])
    pre_high = float(premarket["High"].max())
    pre_low = float(premarket["Low"].min())
    pre_close = float(premarket.iloc[-1]["Close"])

    change_pct = (
        (pre_close - previous_close)
        / previous_close
    ) * 100

    if change_pct > 0:
        direction = "GREEN"

    elif change_pct < 0:
        direction = "RED"

    else:
        direction = "DOJI"

    return {
        "Pre-Market Open": pre_open,
        "Pre-Market High": pre_high,
        "Pre-Market Low": pre_low,
        "Pre-Market Price": pre_close,
        "Change %": change_pct,
        "Direction": direction,
        "Previous Close": previous_close
    }


# ============================================================
# ANALYZE ONE STOCK
# ============================================================

def analyze_stock(symbol, df):

    if df is None or df.empty:
        return None

    today = datetime.now(IST).date()

    today_data = df[
        df.index.date == today
    ].copy()

    if today_data.empty:
        return None

    regular = today_data[
        (today_data.index.time >= MARKET_OPEN) &
        (today_data.index.time < MARKET_CLOSE)
    ].copy()

    result = {
        "Symbol": symbol,
        "Sector": STOCK_SECTOR[symbol]
    }

    # --------------------------------------------------------
    # PRE-MARKET
    # --------------------------------------------------------

    pre = get_premarket_analysis(
        df,
        today
    )

    result["PRE"] = pre

    # --------------------------------------------------------
    # 2 MINUTE
    # --------------------------------------------------------

    result["2M"] = aggregate_window(
        regular,
        MARKET_OPEN,
        TWO_MIN_END,
        2
    )

    # --------------------------------------------------------
    # 5 MINUTE
    # --------------------------------------------------------

    result["5M"] = aggregate_window(
        regular,
        MARKET_OPEN,
        FIVE_MIN_END,
        5
    )

    # --------------------------------------------------------
    # 15 MINUTE
    # --------------------------------------------------------

    result["15M"] = aggregate_window(
        regular,
        MARKET_OPEN,
        FIFTEEN_MIN_END,
        15
    )

    return result


# ============================================================
# SCAN ALL STOCKS
# ============================================================

def scan_market():

    results = []

    progress = st.progress(0)

    status = st.empty()

    batch_size = 35

    total = len(ALL_STOCKS)

    completed = 0

    for start in range(
        0,
        total,
        batch_size
    ):

        batch_symbols = ALL_STOCKS[
            start:start + batch_size
        ]

        status.info(
            f"Downloading {start + 1} - "
            f"{min(start + batch_size, total)} "
            f"of {total} stocks..."
        )

        raw_data = download_batch(
            tuple(batch_symbols)
        )

        for symbol in batch_symbols:

            df = extract_stock_data(
                raw_data,
                symbol
            )

            if df is not None:

                analysis = analyze_stock(
                    symbol,
                    df
                )

                if analysis is not None:
                    results.append(analysis)

            completed += 1

            progress.progress(
                min(
                    completed / total,
                    1.0
                )
            )

    status.success(
        f"Scan complete — {len(results)} stocks received."
    )

    progress.empty()

    return results


# ============================================================
# CONVERT TIMEFRAME RESULTS TO DATAFRAME
# ============================================================

def timeframe_dataframe(results, timeframe):

    rows = []

    for result in results:

        data = result.get(timeframe)

        if data is None:
            continue

        row = {
            "Symbol": result["Symbol"],
            "Sector": result["Sector"]
        }

        row.update(data)

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


# ============================================================
# PREMARKET DATAFRAME
# ============================================================

def premarket_dataframe(results):

    rows = []

    for result in results:

        data = result.get("PRE")

        if data is None:
            continue

        row = {
            "Symbol": result["Symbol"],
            "Sector": result["Sector"]
        }

        row.update(data)

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


# ============================================================
# SECTOR HEATMAP
# ============================================================

def create_sector_heatmap(df):

    if df.empty:
        return pd.DataFrame()

    heatmap = (
        df.groupby("Sector")
        .agg(
            Stocks=("Symbol", "count"),
            Avg_Change=("Change %", "mean"),
            Green=("Candle", lambda x:
                   (x == "GREEN").sum()),
            Red=("Candle", lambda x:
                 (x == "RED").sum())
        )
        .reset_index()
    )

    heatmap["Green %"] = (
        heatmap["Green"]
        / heatmap["Stocks"]
    ) * 100

    heatmap = heatmap.sort_values(
        "Avg_Change",
        ascending=False
    )

    return heatmap


# ============================================================
# PREMARKET SECTOR HEATMAP
# ============================================================

def create_premarket_heatmap(df):

    if df.empty:
        return pd.DataFrame()

    heatmap = (
        df.groupby("Sector")
        .agg(
            Stocks=("Symbol", "count"),
            Avg_Change=("Change %", "mean"),
            Gainers=("Direction",
                     lambda x:
                     (x == "GREEN").sum()),
            Losers=("Direction",
                   lambda x:
                   (x == "RED").sum())
        )
        .reset_index()
    )

    heatmap["Gainer %"] = (
        heatmap["Gainers"]
        / heatmap["Stocks"]
    ) * 100

    return heatmap.sort_values(
        "Avg_Change",
        ascending=False
    )


# ============================================================
# BUY / SELL RANKING
# ============================================================

def rank_buy_stocks(
    df,
    top_sector,
    n=3
):

    if df.empty or top_sector is None:
        return pd.DataFrame()

    buy = df[
        (df["Sector"] == top_sector) &
        (df["Candle"] == "GREEN")
    ].copy()

    if buy.empty:
        return pd.DataFrame()

    buy["OpenLowPriority"] = np.where(
        buy["Open Status"] == "OPEN=LOW",
        1,
        0
    )

    buy = buy.sort_values(
        [
            "OpenLowPriority",
            "Change %"
        ],
        ascending=[
            False,
            False
        ]
    )

    buy.insert(
        0,
        "Priority",
        range(1, len(buy) + 1)
    )

    return buy.head(n)


def rank_sell_stocks(
    df,
    bottom_sector,
    n=3
):

    if df.empty or bottom_sector is None:
        return pd.DataFrame()

    sell = df[
        (df["Sector"] == bottom_sector) &
        (df["Candle"] == "RED")
    ].copy()

    if sell.empty:
        return pd.DataFrame()

    sell["OpenHighPriority"] = np.where(
        sell["Open Status"] == "OPEN=HIGH",
        1,
        0
    )

    sell = sell.sort_values(
        [
            "OpenHighPriority",
            "Change %"
        ],
        ascending=[
            False,
            True
        ]
    )

    sell.insert(
        0,
        "Priority",
        range(1, len(sell) + 1)
    )

    return sell.head(n)


# ============================================================
# PREMARKET TOP GAINERS / LOSERS
# ============================================================

def rank_premarket_gainers(df, n=3):

    if df.empty:
        return pd.DataFrame()

    return df.sort_values(
        "Change %",
        ascending=False
    ).head(n)


def rank_premarket_losers(df, n=3):

    if df.empty:
        return pd.DataFrame()

    return df.sort_values(
        "Change %",
        ascending=True
    ).head(n)


# ============================================================
# DISPLAY STOCK TABLE
# ============================================================

def display_stock_table(
    df,
    trade_type=None
):

    if df.empty:

        st.info(
            "इस timeframe में अभी qualifying stock नहीं मिला।"
        )

        return

    columns = [
        "Priority",
        "Symbol",
        "Sector",
        "Change %",
        "Candle",
        "Open Status",
        "Open",
        "High",
        "Low",
        "Close"
    ]

    available = [
        col for col in columns
        if col in df.columns
    ]

    display_df = df[available].copy()

    if "Change %" in display_df.columns:
        display_df["Change %"] = (
            display_df["Change %"]
            .round(2)
        )

    for col in [
        "Open",
        "High",
        "Low",
        "Close"
    ]:

        if col in display_df.columns:
            display_df[col] = (
                display_df[col]
                .round(2)
            )

    if trade_type:

        display_df["Trade"] = trade_type

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# DISPLAY TIMEFRAME
# ============================================================

def display_timeframe(
    results,
    timeframe,
    title,
    description
):

    st.subheader(title)

    st.caption(description)

    df = timeframe_dataframe(
        results,
        timeframe
    )

    if df.empty:

        if timeframe == "15M":

            st.warning(
                "⏳ First 15-minute candle "
                "9:30 AM पर complete होगी।"
            )

        else:

            st.warning(
                "इस timeframe का data अभी उपलब्ध नहीं है।"
            )

        return None, None, None

    heatmap = create_sector_heatmap(df)

    if heatmap.empty:
        return df, None, None

    top_gainer_sector = heatmap.iloc[0]["Sector"]

    top_loser_sector = heatmap.iloc[-1]["Sector"]

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "🟢 Top Gainer Sector",
            top_gainer_sector,
            f"{heatmap.iloc[0]['Avg_Change']:.2f}%"
        )

    with col2:

        st.metric(
            "🔴 Top Loser Sector",
            top_loser_sector,
            f"{heatmap.iloc[-1]['Avg_Change']:.2f}%"
        )

    st.markdown("### 📊 Sector Heatmap")

    heatmap_display = heatmap.copy()

    heatmap_display["Avg_Change"] = (
        heatmap_display["Avg_Change"]
        .round(2)
    )

    heatmap_display["Green %"] = (
        heatmap_display["Green %"]
        .round(1)
    )

    heatmap_display = heatmap_display.rename(
        columns={
            "Avg_Change": "Avg Change %",
            "Green": "Green Stocks",
            "Red": "Red Stocks"
        }
    )

    st.dataframe(
        heatmap_display,
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # BUY
    # --------------------------------------------------------

    st.markdown(
        f"### 🟢 BUY — {top_gainer_sector}"
    )

    buy = rank_buy_stocks(
        df,
        top_gainer_sector,
        3
    )

    if not buy.empty:

        st.success(
            "Priority: OPEN=LOW + GREEN → "
            "Highest priority"
        )

        display_stock_table(
            buy,
            "BUY"
        )

    else:

        st.info(
            "Top Gainer Sector में GREEN "
            "qualifying stock नहीं मिला।"
        )

    # --------------------------------------------------------
    # SELL
    # --------------------------------------------------------

    st.markdown(
        f"### 🔴 SELL — {top_loser_sector}"
    )

    sell = rank_sell_stocks(
        df,
        top_loser_sector,
        3
    )

    if not sell.empty:

        st.error(
            "Priority: OPEN=HIGH + RED → "
            "Highest priority"
        )

        display_stock_table(
            sell,
            "SELL"
        )

    else:

        st.info(
            "Top Loser Sector में RED "
            "qualifying stock नहीं मिला।"
        )

    return df, buy, sell


# ============================================================
# PREMARKET DISPLAY
# ============================================================

def display_premarket(results):

    st.subheader(
        "🌅 Pre-Market / Pre-Open"
    )

    st.caption(
        "Yahoo Finance feed में pre-market data "
        "उपलब्ध होने पर ही यह section populated होगा।"
    )

    df = premarket_dataframe(results)

    if df.empty:

        st.warning(
            "NSE Pre-Open data इस feed में उपलब्ध नहीं है। "
            "इसे N/A मानें — कोई अनुमानित data नहीं बनाया गया है।"
        )

        return

    heatmap = create_premarket_heatmap(df)

    if not heatmap.empty:

        top_sector = heatmap.iloc[0]["Sector"]
        bottom_sector = heatmap.iloc[-1]["Sector"]

        c1, c2 = st.columns(2)

        with c1:

            st.metric(
                "🟢 Pre-Market Gainer Sector",
                top_sector,
                f"{heatmap.iloc[0]['Avg_Change']:.2f}%"
            )

        with c2:

            st.metric(
                "🔴 Pre-Market Loser Sector",
                bottom_sector,
                f"{heatmap.iloc[-1]['Avg_Change']:.2f}%"
            )

        st.markdown(
            "### 📊 Pre-Market Sector Heatmap"
        )

        display_heatmap = heatmap.copy()

        display_heatmap["Avg_Change"] = (
            display_heatmap["Avg_Change"]
            .round(2)
        )

        display_heatmap["Gainer %"] = (
            display_heatmap["Gainer %"]
            .round(1)
        )

        display_heatmap = display_heatmap.rename(
            columns={
                "Avg_Change": "Avg Change %",
                "Gainers": "Gainer Stocks",
                "Losers": "Loser Stocks"
            }
        )

        st.dataframe(
            display_heatmap,
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------
    # TOP GAINERS / LOSERS
    # --------------------------------------------------------

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            "### 🟢 Top 3 Pre-Market Gainers"
        )

        gainers = rank_premarket_gainers(
            df,
            3
        )

        if not gainers.empty:

            gain_display = gainers[
                [
                    "Symbol",
                    "Sector",
                    "Change %",
                    "Pre-Market Price"
                ]
            ].copy()

            gain_display["Change %"] = (
                gain_display["Change %"]
                .round(2)
            )

            st.dataframe(
                gain_display,
                use_container_width=True,
                hide_index=True
            )

    with c2:

        st.markdown(
            "### 🔴 Top 3 Pre-Market Losers"
        )

        losers = rank_premarket_losers(
            df,
            3
        )

        if not losers.empty:

            loss_display = losers[
                [
                    "Symbol",
                    "Sector",
                    "Change %",
                    "Pre-Market Price"
                ]
            ].copy()

            loss_display["Change %"] = (
                loss_display["Change %"]
                .round(2)
            )

            st.dataframe(
                loss_display,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# MAIN APP
# ============================================================

now_ist = datetime.now(IST)

st.info(
    f"🕒 Current IST Time: "
    f"{now_ist.strftime('%d-%m-%Y %H:%M:%S')}"
)


st.markdown(
    """
### Scanner Logic

**Pre-Market**
→ Pre-open / pre-market movement

**First 2 Minutes**
→ 09:15–09:17

**First 5 Minutes**
→ 09:15–09:20  
→ मुख्य 9:20 trading signal

**First 15 Minutes**
→ 09:15–09:30  
→ 9:30 के बाद complete

**BUY Priority**
→ GREEN + OPEN=LOW

**SELL Priority**
→ RED + OPEN=HIGH
"""
)


# ============================================================
# SCAN BUTTON
# ============================================================

scan_button = st.button(
    "🚀 RUN LIVE F&O SCAN",
    type="primary",
    use_container_width=True
)


if scan_button:

    with st.spinner(
        "NSE F&O stocks का live intraday data scan हो रहा है..."
    ):

        results = scan_market()

    if not results:

        st.error(
            "कोई market data प्राप्त नहीं हुआ। "
            "कुछ देर बाद फिर scan करें।"
        )

        st.stop()

    st.session_state["scan_results"] = results

    st.session_state["scan_time"] = (
        datetime.now(IST)
        .strftime("%d-%m-%Y %H:%M:%S")
    )


# ============================================================
# DISPLAY RESULTS
# ============================================================

if "scan_results" in st.session_state:

    results = st.session_state["scan_results"]

    st.success(
        f"Last Scan: "
        f"{st.session_state.get('scan_time', 'N/A')}"
    )

    # ========================================================
    # PRE-MARKET
    # ========================================================

    display_premarket(results)

    st.divider()

    # ========================================================
    # TABS
    # ========================================================

    tab2, tab5, tab15 = st.tabs(
        [
            "⏱ First 2 Minutes",
            "🔥 First 5 Minutes — 9:20",
            "🕘 First 15 Minutes"
        ]
    )

    # ========================================================
    # 2 MINUTE
    # ========================================================

    with tab2:

        display_timeframe(
            results,
            "2M",
            "⏱ First 2-Minute Gainer / Loser",
            "09:15–09:17 | GREEN / RED + OPEN=LOW / OPEN=HIGH"
        )

    # ========================================================
    # 5 MINUTE
    # ========================================================

    with tab5:

        st.markdown(
            "## 🔥 9:20 PRIMARY TRADE SCANNER"
        )

        st.warning(
            "9:20 Trade Logic: "
            "Top Gainer Sector → GREEN + OPEN=LOW "
            "| "
            "Top Loser Sector → RED + OPEN=HIGH"
        )

        df5, buy5, sell5 = display_timeframe(
            results,
            "5M",
            "🔥 First 5-Minute Gainer / Loser",
            "09:15–09:20 | Primary 9:20 signal"
        )

        # ----------------------------------------------------
        # FINAL TRADE WATCH
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "🎯 FINAL 9:20 TRADE WATCH"
        )

        if (
            buy5 is not None
            and not buy5.empty
        ):

            best_buy = buy5.iloc[0]

            st.success(
                f"🟢 BUY WATCH: "
                f"{best_buy['Symbol']} | "
                f"{best_buy['Sector']} | "
                f"{best_buy['Change %']:.2f}% | "
                f"{best_buy['Open Status']}"
            )

        else:

            st.info(
                "No qualified BUY setup."
            )

        if (
            sell5 is not None
            and not sell5.empty
        ):

            best_sell = sell5.iloc[0]

            st.error(
                f"🔴 SELL WATCH: "
                f"{best_sell['Symbol']} | "
                f"{best_sell['Sector']} | "
                f"{best_sell['Change %']:.2f}% | "
                f"{best_sell['Open Status']}"
            )

        else:

            st.info(
                "No qualified SELL setup."
            )

    # ========================================================
    # 15 MINUTE
    # ========================================================

    with tab15:

        display_timeframe(
            results,
            "15M",
            "🕘 First 15-Minute Gainer / Loser",
            "09:15–09:30 | Complete result available after 9:30 AM"
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Suman F&O Multi-Timeframe Scanner | "
    "Data source: Yahoo Finance | "
    "For research / educational use only"
)
