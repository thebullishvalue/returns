import streamlit as st
import pandas as pd
import yfinance as yf
import io
import numpy as np
import time
from datetime import datetime, timedelta

# --- System Configuration ---
st.set_page_config(
    page_title="Portfolio Returns Tracker", 
    page_icon="📈", 
    layout="wide", 
    initial_sidebar_state="expanded"
)
VERSION = "v1.2.0 - Returns Engine"

# --- CSS Styling (Exact Match from app.py) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        --primary-color: #FFC300;
        --primary-rgb: 255, 195, 0;
        --background-color: #0F0F0F;
        --secondary-background-color: #1A1A1A;
        --bg-card: #1A1A1A;
        --bg-elevated: #2A2A2A;
        --text-primary: #EAEAEA;
        --text-secondary: #EAEAEA;
        --text-muted: #888888;
        --border-color: #2A2A2A;
        --border-light: #3A3A3A;
        
        --success-green: #10b981;
        --danger-red: #ef4444;
        --warning-amber: #f59e0b;
        --info-cyan: #06b6d4;
        --neutral: #888888;
    }
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main, [data-testid="stSidebar"] {
        background-color: var(--background-color);
        color: var(--text-primary);
    }
    
    .stApp > header {
        background-color: transparent;
    }
    
    .block-container {
        padding-top: 1rem;
        max-width: 1400px;
    }
    
    .premium-header {
        background: var(--secondary-background-color);
        padding: 1.25rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 0 20px rgba(var(--primary-rgb), 0.1);
        border: 1px solid var(--border-color);
        position: relative;
        overflow: hidden;
        margin-top: 2.5rem;
    }
    
    .premium-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 20% 50%, rgba(var(--primary-rgb),0.08) 0%, transparent 50%);
        pointer-events: none;
    }
    
    .premium-header h1 {
        margin: 0;
        font-size: 2.50rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.50px;
        position: relative;
    }
    
    .premium-header .tagline {
        color: var(--text-muted);
        font-size: 1rem;
        margin-top: 0.25rem;
        font-weight: 400;
        position: relative;
    }
    
    .metric-card {
        background-color: var(--bg-card);
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid var(--border-color);
        box-shadow: 0 0 15px rgba(var(--primary-rgb), 0.08);
        margin-bottom: 0.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        border-color: var(--border-light);
    }
    
    .metric-card h4 {
        color: var(--text-muted);
        font-size: 0.8rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-card h2 {
        color: var(--text-primary);
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        line-height: 1;
    }
    
    .metric-card .sub-metric {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    .metric-card.success h2 { color: var(--success-green); }
    .metric-card.danger h2 { color: var(--danger-red); }
    .metric-card.warning h2 { color: var(--warning-amber); }
    .metric-card.info h2 { color: var(--info-cyan); }
    .metric-card.neutral h2 { color: var(--neutral); }
    .metric-card.primary h2 { color: var(--primary-color); }
    .metric-card.white h2 { color: var(--text-primary); }
    
    .info-box {
        background: var(--secondary-background-color);
        border: 1px solid var(--border-color);
        border-left: 4px solid var(--primary-color);
        padding: 1.25rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        box-shadow: 0 0 15px rgba(var(--primary-rgb), 0.08);
    }
    
    .info-box h4 {
        color: var(--primary-color);
        margin: 0 0 0.5rem 0;
        font-size: 1rem;
        font-weight: 700;
    }

    /* Buttons */
    .stButton>button {
        border: 2px solid var(--primary-color);
        background: transparent;
        color: var(--primary-color);
        font-weight: 700;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(var(--primary-rgb), 0.6);
        background: var(--primary-color);
        color: #1A1A1A;
        transform: translateY(-2px);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        color: var(--text-muted);
        border-bottom: 2px solid transparent;
        transition: color 0.3s, border-bottom 0.3s;
    }
    .stTabs [aria-selected="true"] {
        color: var(--primary-color);
        border-bottom: 2px solid var(--primary-color);
    }
    .stDataFrame {
        border-radius: 12px;
        background-color: var(--secondary-background-color);
        padding: 10px;
        border: 1px solid var(--border-color);
        box-shadow: 0 0 25px rgba(var(--primary-rgb), 0.1);
    }
    h2 {
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 10px;
    }
    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, var(--border-color) 50%, transparent 100%);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

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

# --- Sidebar Controls ---
with st.sidebar:
    st.markdown("# Configuration")
    
    st.markdown("### Data Input")
    uploaded_file = st.file_uploader("Upload Portfolio CSV", type=["csv"], help="CSV must contain 'symbol', 'units', and 'value' columns.")
    
    st.markdown("### Market Settings")
    market_type = st.radio(
        "Select Market Type",
        ("Global", "Indian"),
        help="Select 'Indian' to append '.NS' to symbols for NSE."
    )
    
    st.markdown("---")
    
    st.markdown("### Valuation Date")
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
    
    st.markdown("---")
    
    run_button = st.button("Fetch Valuations", width='stretch', type="primary")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### Platform Info")
    st.markdown(f"""
    <div class='info-box'>
        <p style='font-size: 0.85rem; margin: 0; color: var(--text-muted); line-height: 1.6;'>
            <strong>Version:</strong> {VERSION}<br>
            <strong>Engine:</strong> Yahoo Finance API<br> 
            <strong>Family:</strong> Pragyam Suite
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Main Application Logic ---
st.markdown(f"""
<div class="premium-header">
    <h1>Portfolio Returns Tracker</h1>
    <div class="tagline">Real-time valuation and performance tracking engine</div>
</div>
""", unsafe_allow_html=True)

if run_button and uploaded_file is not None:
    try:
        # Load data
        portfolio_df = pd.read_csv(uploaded_file)
        
        # Validate required columns
        required_cols = ['symbol', 'units', 'value']
        if not all(col in portfolio_df.columns for col in required_cols):
            st.error(f"CSV must contain the following columns: {', '.join(required_cols)}")
        else:
            with st.spinner("Processing portfolio data..."):
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
                    st.success(f"✅ Valuation Update Complete (As of {date_display})!")
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

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <h4>Original Investment</h4>
            <h2>${total_original_value:,.2f}</h2>
            <div class='sub-metric'>Initial Capital Deployed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        date_label = st.session_state.valuation_date_label
        st.markdown(f"""
        <div class='metric-card primary'>
            <h4>Valuation ({date_label})</h4>
            <h2>${total_current_value:,.2f}</h2>
            <div class='sub-metric'>Market Value at selected date</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card {pl_class}'>
            <h4>Total P/L</h4>
            <h2>${total_return_dollar:,.2f}</h2>
            <div class='sub-metric'>{total_return_percent:,.2f}% Return</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Symbol Level Table ---
    tab1, tab2 = st.tabs(["**Detailed Holdings**", "**Visual Analysis**"])
    
    with tab1:
        st.subheader("Symbol Level Returns")
        
        display_df = results_df[[
            'symbol', 
            'units', 
            'original_value', 
            'latest_price', 
            'current_value', 
            'return_$', 
            'return_%'
        ]].copy()
        
        # We use st.dataframe but in a container styled by the CSS above
        st.dataframe(
            display_df.style
            .format({
                'original_value': '${:,.2f}',
                'latest_price': '${:,.2f}',
                'current_value': '${:,.2f}',
                'return_$': '${:,.2f}',
                'return_%': '{:,.2f}%',
                'units': '{:,.2f}'
            })
            .background_gradient(
                cmap='RdYlGn', 
                subset=['return_%'],
                vmin=-10, 
                vmax=10 
            ),
            use_container_width=True,
            height=500
        )
    
    with tab2:
        st.subheader("Performance Visualization")
        # Reuse code structure from logic, but visualize
        import plotly.express as px
        
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
    # --- Welcome State (Matches app.py style) ---
    st.markdown("""
    <div class='info-box welcome'>
        <h4>Welcome to the Returns Tracker</h4>
        <p>
            This module allows you to track the real-time or historical performance of your portfolios.
            It uses market data to compute valuations against your original cost basis.
        </p>
        <strong>To begin, please follow these steps:</strong>
        <ol style="margin-left: 20px; margin-top: 10px;">
            <li>Prepare a CSV file with columns: <code>symbol</code>, <code>units</code>, <code>value</code> (original cost).</li>
            <li>Upload the file in the sidebar configuration panel.</li>
            <li>Select the <strong>Market Type</strong> (Global or Indian).</li>
            <li>Choose <strong>Valuation Mode</strong> (Live for today, or Historical for a past date).</li>
            <li>Click <strong>Fetch Valuations</strong>.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='metric-card info'>
            <h4>FLEXIBLE DATA</h4>
            <h2>Time Travel</h2>
            <div class='sub-metric'>Live or Historical Valuations</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card success'>
            <h4>INSTANT</h4>
            <h2>P/L Analysis</h2>
            <div class='sub-metric'>Automatic Calculation</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='metric-card primary'>
            <h4>VISUAL</h4>
            <h2>Insights</h2>
            <div class='sub-metric'>Interactive Charts</div>
        </div>
        """, unsafe_allow_html=True)

# --- Footer ---
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.caption(f"© {datetime.now().year} Returns Trackker | Hemrek Capital | {VERSION} | Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S IST')}")
