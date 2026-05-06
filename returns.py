import streamlit as st
import pandas as pd
import yfinance as yf
import io
import os
from datetime import datetime, timedelta, timezone
import plotly.express as px

# --- System Configuration ---
st.set_page_config(
    page_title="Returns | Portfolio Returns Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)
VERSION = "v1.3.1 - Returns Engine" # Bumped version for Excel support

# Load CSS from external file
_css_path = os.path.join(os.path.dirname(__file__), "style.css")
try:
    with open(_css_path, encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# --- Application State ---
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'results' not in st.session_state:
    st.session_state.results = pd.DataFrame()
if 'valuation_date_label' not in st.session_state:
    st.session_state.valuation_date_label = "Latest / Live"

# --- Helper Function ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
def fetch_prices(tickers: list, target_date=None) -> pd.Series:
    """
    Fetches closing prices.
    If target_date is None, fetches latest available (live/recent close).
    If target_date is provided, fetches the close on that date (or most recent trading day before it).
    """
    try:
        if target_date is None:
            # Live/Latest logic: Fetch last 5 days to ensure coverage over weekends/holidays
            data = yf.download(tickers, period="5d", progress=False)
        else:
            # Historical logic: Window ending on target_date + 1 (exclusive)
            # Look back 10 days to ensure we find a trading day
            end_dt = target_date + timedelta(days=1)
            start_dt = target_date - timedelta(days=10)
            data = yf.download(tickers, start=start_dt, end=end_dt, progress=False)

        if data.empty:
            return pd.Series(dtype=float)

        # Get the 'Close' prices
        # Handle cases where columns might be multi-level if yfinance version varies
        try:
            close_prices = data['Close']
        except KeyError:
            return pd.Series(dtype=float)

        if close_prices.empty:
             return pd.Series(dtype=float)

        if len(tickers) == 1:
            # If single ticker, close_prices is a Series (Index=Date)
            # We return a Series with index=[Ticker] and value=Price to ensure it maps correctly
            last_price = close_prices.iloc[-1]
            return pd.Series(data=[last_price], index=[tickers[0]])

        # For multiple tickers, close_prices is a DataFrame (Index=Date, Columns=Tickers)
        # Get the last row (most recent date in the range)
        latest_prices = close_prices.iloc[-1]
        return latest_prices

    except Exception as e:
        st.error(f"Error fetching data from yfinance: {e}")
        return pd.Series(dtype=float)


# --- UI Primitives ---
def _section_header(title: str, subtitle: str = "") -> str:
    """Generate styled section header HTML."""
    sub = f"<p class='section-subtitle'>{subtitle}</p>" if subtitle else ""
    return f"<div class='section'><div class='section-header'><h3 class='section-title'>{title}</h3>{sub}</div></div>"


def _section_divider():
    """Render section divider."""
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


def _metric_card(label: str, value: str, sub: str = "", cls: str = "neutral") -> str:
    """Generate metric card HTML."""
    sub_html = f"<div class='sub-metric'>{sub}</div>" if sub else ""
    return f"<div class='metric-card {cls}'><h4>{label}</h4><h2>{value}</h2>{sub_html}</div>"


# --- Sidebar Controls ---
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1rem 0; margin-bottom:1rem;">
        <div style="font-size:1.75rem; font-weight:800; color:#FFC300;">RETURNS</div>
        <div style="color:#888; font-size:0.75rem; margin-top:0.25rem;">Portfolio Returns Tracker</div>
    </div>
    """, unsafe_allow_html=True)
    _section_divider()

    st.markdown('<div class="sidebar-title">📂 Data Input</div>', unsafe_allow_html=True)
    
    # Updated to accept Excel files
    uploaded_file = st.file_uploader(
        "Upload Portfolio File", 
        type=["csv", "xlsx", "xls"], 
        help="File must be CSV or Excel and contain 'symbol', 'units', and 'value' columns."
    )

    st.markdown('<div class="sidebar-title">🌍 Market Settings</div>', unsafe_allow_html=True)
    market_type = st.radio(
        "Select Market Type",
        ("Global", "Indian"),
        help="Select 'Indian' to append '.NS' to symbols for NSE."
    )

    _section_divider()

    st.markdown('<div class="sidebar-title">📅 Valuation Date</div>', unsafe_allow_html=True)
    date_mode = st.radio(
        "Valuation Mode",
        ["Live / Latest", "Historical Date"],
        help="Choose 'Live' for current market prices or 'Historical' to check portfolio value on a specific past date."
    )

    selected_valuation_date = None
    if date_mode == "Historical Date":
        selected_valuation_date = st.date_input(
            "Select Date",
            value=datetime.today() - timedelta(days=1),
            max_value=datetime.today()
        )

    _section_divider()

    run_button = st.button("Fetch Valuations", width='stretch', type="primary")
    status_placeholder = st.empty() # Placeholder for success message

    _section_divider()
    st.markdown(f"""
    <div class='info-box'>
        <p style='font-size:0.8rem; margin:0; color:var(--text-muted); line-height:1.5;'>
            <strong>Version:</strong> {VERSION}<br>
            <strong>Engine:</strong> Yahoo Finance API<br>
            <strong>Family:</strong> Hemrek Suite
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Main Application Logic ---
st.markdown(f"""
<div class="premium-header">
    <h1>RETURNS | Portfolio Returns Tracker</h1>
    <div class="tagline">Real-time valuation and performance tracking engine</div>
</div>
""", unsafe_allow_html=True)

if run_button and uploaded_file is not None:
    try:
        # Load data based on file extension
        if uploaded_file.name.endswith('.csv'):
            portfolio_df = pd.read_csv(uploaded_file)
        else:
            portfolio_df = pd.read_excel(uploaded_file)
        
        # Validate required columns
        required_cols = ['symbol', 'units', 'value']
        
        # Convert columns to lowercase temporarily to do a case-insensitive check
        lower_cols = [col.lower() for col in portfolio_df.columns]
        
        if not all(col in lower_cols for col in required_cols):
            st.error(f"File must contain the following columns: {', '.join(required_cols)}")
        else:
            with st.spinner("Processing portfolio data..."):
                # Standardize column names if they were uppercase in Excel
                portfolio_df.columns = [col.lower() for col in portfolio_df.columns]
                
                # Prepare DataFrame
                portfolio = portfolio_df[['symbol', 'units', 'value']].copy()
                portfolio.rename(columns={'value': 'original_value'}, inplace=True)
                
                # Apply market logic
                if market_type == "Indian":
                    portfolio['ticker'] = portfolio['symbol'].astype(str) + ".NS"
                else:
                    portfolio['ticker'] = portfolio['symbol'].astype(str)
                
                tickers = portfolio['ticker'].tolist()

            # Prepare Date Argument
            target_date_arg = selected_valuation_date if date_mode == "Historical Date" else None
            
            # Fetch data from yfinance
            date_display = str(target_date_arg) if target_date_arg else "Latest Live"
            toast_msg = f"Fetching prices ({date_display}) for {len(tickers)} symbols..."
            st.toast(toast_msg, icon="⏳")
            
            latest_prices = fetch_prices(tickers, target_date_arg)
            
            if latest_prices.empty:
                st.error("Could not fetch any data from yfinance. Please check your symbols and market type.")
            else:
                portfolio['latest_price'] = portfolio['ticker'].map(latest_prices)
                
                # Handle failed fetches
                failed_fetches = portfolio[portfolio['latest_price'].isna()]['symbol'].tolist()
                if failed_fetches:
                    st.warning(f"Could not fetch data for: {', '.join(failed_fetches)}. These will be excluded.")
                    portfolio.dropna(subset=['latest_price'], inplace=True)

                if not portfolio.empty:
                    # Calculate returns
                    portfolio['current_value'] = portfolio['latest_price'] * portfolio['units']
                    portfolio['return_$'] = portfolio['current_value'] - portfolio['original_value']
                    portfolio['return_%'] = (portfolio['return_$'] / portfolio['original_value']) * 100
                    
                    # Store in session state
                    st.session_state.results = portfolio
                    st.session_state.data_loaded = True
                    st.session_state.valuation_date_label = date_display
                    
                    # Update status in sidebar placeholder
                    status_placeholder.success(f"✅ Valuation Update Complete (As of {date_display})!")
                else:
                    st.error("No valid data to display after fetching prices.")
                    st.session_state.data_loaded = False
                        
    except Exception as e:
        st.error(f"An error occurred during processing: {e}")
        st.session_state.data_loaded = False

# --- Display Results ---
if st.session_state.data_loaded:
    results_df = st.session_state.results

    # --- Portfolio Level Cards ---
    total_original_value = results_df['original_value'].sum()
    total_current_value = results_df['current_value'].sum()
    total_return_dollar = results_df['return_$'].sum()

    # Avoid division by zero
    if total_original_value != 0:
        total_return_percent = (total_return_dollar / total_original_value) * 100
    else:
        total_return_percent = 0.0

    # Determine P/L Color class
    if total_return_dollar > 0:
        pl_class = "success"
    elif total_return_dollar < 0:
        pl_class = "danger"
    else:
        pl_class = "neutral"

    # Top metrics strip
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(_metric_card("Original Investment", f"${total_original_value:,.2f}", "Initial Capital Deployed", "primary"), unsafe_allow_html=True)
    with mc2:
        date_label = st.session_state.valuation_date_label
        st.markdown(_metric_card(f"Valuation ({date_label})", f"${total_current_value:,.2f}", "Market Value at selected date", "info"), unsafe_allow_html=True)
    with mc3:
        st.markdown(_metric_card("Total P/L", f"${total_return_dollar:,.2f}", f"{total_return_percent:,.2f}% Return", pl_class), unsafe_allow_html=True)
    with mc4:
        num_positions = len(results_df)
        st.markdown(_metric_card("Positions", str(num_positions), "Active holdings", "neutral"), unsafe_allow_html=True)

    _section_divider()

    # --- Symbol Level Table ---
    tab1, tab2 = st.tabs(["**Detailed Holdings**", "**Visual Analysis**"])

    with tab1:
        st.markdown(_section_header(
            "Symbol Level Returns",
            f"{len(results_df)} positions · performance breakdown"
        ), unsafe_allow_html=True)

        display_df = results_df[[
            'symbol',
            'units',
            'original_value',
            'latest_price',
            'current_value',
            'return_$',
            'return_%'
        ]].copy()

        # Rename columns for display
        display_df = display_df.rename(columns={
            'symbol': 'Symbol',
            'units': 'Units',
            'original_value': 'Original Value ($)',
            'latest_price': 'Latest Price ($)',
            'current_value': 'Current Value ($)',
            'return_$': 'P/L ($)',
            'return_%': 'P/L (%)'
        })

        # We use st.dataframe but in a container styled by the CSS above
        st.dataframe(
            display_df.style
            .format({
                'Original Value ($)': '${:,.2f}',
                'Latest Price ($)': '${:,.2f}',
                'Current Value ($)': '${:,.2f}',
                'P/L ($)': '${:,.2f}',
                'P/L (%)': '{:,.2f}%',
                'Units': '{:,.2f}'
            })
            .background_gradient(
                cmap='RdYlGn',
                subset=['P/L (%)'],
                vmin=-10,
                vmax=10
            ),
            use_container_width=True,
            height=500
        )

        _section_divider()

        # CSV Download
        first_cols = ['Symbol', 'Units', 'Original Value ($)']
        other_cols = [c for c in display_df.columns if c not in first_cols]
        download_df = display_df[first_cols + other_cols]
        buf = io.BytesIO()
        download_df.to_csv(buf, index=False, encoding="utf-8-sig")
        st.download_button(
            label="Download Portfolio CSV",
            data=buf.getvalue(),
            file_name=f"returns_portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            width='stretch',
            key="returns_csv_download",
        )

    with tab2:
        st.markdown(_section_header(
            "Performance Visualization",
            "Portfolio allocation and returns analysis"
        ), unsafe_allow_html=True)

        col_viz1, col_viz2 = st.columns(2)

        with col_viz1:
             fig_alloc = px.pie(
                 results_df,
                 values='current_value',
                 names='symbol',
                 title='Portfolio Allocation (Current Value)',
                 hole=0.4
             )
             fig_alloc.update_layout(template='plotly_dark')
             st.plotly_chart(fig_alloc, use_container_width=True)

        with col_viz2:
             fig_bar = px.bar(
                 results_df,
                 x='symbol',
                 y='return_%',
                 color='return_%',
                 color_continuous_scale='RdYlGn',
                 title='Return % by Symbol'
             )
             fig_bar.update_layout(template='plotly_dark')
             st.plotly_chart(fig_bar, use_container_width=True)

else:
    # --- Welcome State (Matches Pragyam style) ---
    st.markdown("""
    <div class='info-box welcome'>
        <h4>Welcome to the Portfolio Returns Tracker</h4>
        <p>
            This module allows you to track the real-time or historical performance of your portfolios.
            It uses market data to compute valuations against your original cost basis.
        </p>
        <strong>To begin, please follow these steps:</strong>
        <ol style="margin-left: 20px; margin-top: 10px;">
            <li>Prepare a <strong>CSV or Excel file</strong> with columns: <code>symbol</code>, <code>units</code>, <code>value</code> (original cost).</li>
            <li>Upload the file in the sidebar configuration panel.</li>
            <li>Select the <strong>Market Type</strong> (Global or Indian).</li>
            <li>Choose <strong>Valuation Mode</strong> (Live for today, or Historical for a past date).</li>
            <li>Click <strong>Fetch Valuations</strong>.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    _section_divider()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""<div class='metric-card info'><h4>FLEXIBLE DATA</h4><h2>Time Travel</h2>
        <div class='sub-metric'>Live or Historical Valuations</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class='metric-card success'><h4>INSTANT</h4><h2>P/L Analysis</h2>
        <div class='sub-metric'>Automatic Calculation</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class='metric-card primary'><h4>VISUAL</h4><h2>Insights</h2>
        <div class='sub-metric'>Interactive Charts</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown("""<div class='metric-card warning'><h4>GLOBAL</h4><h2>Markets</h2>
        <div class='sub-metric'>Multiple exchanges</div></div>""", unsafe_allow_html=True)

# --- Footer ---
_section_divider()
ist = timezone(offset=timedelta(hours=5, minutes=30))
now_ist = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")
st.markdown(f"""
<div style="text-align:center; padding:1rem 0; color:var(--text-muted); font-size:0.75rem;">
    <span>© 2026 Hemrek Capital</span>
    <span style="margin:0 0.5rem; color:var(--border-light);">|</span>
    <span>{VERSION}</span>
    <span style="margin:0 0.5rem; color:var(--border-light);">|</span>
    <span>{now_ist}</span>
</div>
""", unsafe_allow_html=True)
