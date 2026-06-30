import streamlit as st
import pandas as pd
import yfinance as yf
import io
import os
from datetime import datetime, timedelta, timezone
import plotly.express as px

# --- Swing UI Integration ---
from ui import theme
from ui import components

# --- System Configuration ---
st.set_page_config(
    page_title="Returns | Portfolio Returns Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)
VERSION = "v3.1.0 - Returns Engine (Swing UI Layout)"

# Inject Obsidian Quant Terminal CSS
theme.inject_css()

# --- Application State ---
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "Single Portfolio"
if 'data_loaded_single' not in st.session_state:
    st.session_state.data_loaded_single = False
if 'data_loaded_comp' not in st.session_state:
    st.session_state.data_loaded_comp = False
if 'results_single' not in st.session_state:
    st.session_state.results_single = None
if 'results_comp_1' not in st.session_state:
    st.session_state.results_comp_1 = None
if 'results_comp_2' not in st.session_state:
    st.session_state.results_comp_2 = None
if 'valuation_date_label' not in st.session_state:
    st.session_state.valuation_date_label = "Latest / Live"
if 'comp_names' not in st.session_state:
    st.session_state.comp_names = ("Portfolio 1", "Portfolio 2")

# --- Helper Function ---
@st.cache_data(ttl=600)
def fetch_prices(tickers: list, target_date=None, market_type="Global") -> pd.Series:
    prices = pd.Series(dtype=float)
    try:
        if target_date is None:
            data = yf.download(tickers, period="5d", progress=False)
        else:
            end_dt = target_date + timedelta(days=1)
            start_dt = target_date - timedelta(days=10)
            data = yf.download(tickers, start=start_dt, end=end_dt, progress=False)

        if not data.empty:
            try:
                close_prices = data['Close']
                if not close_prices.empty:
                    if len(tickers) == 1:
                        valid_prices = close_prices.dropna()
                        if not valid_prices.empty:
                            last_price = float(valid_prices.iloc[-1])
                            prices = pd.Series(data=[last_price], index=[tickers[0]])
                    else:
                        prices = close_prices.ffill().iloc[-1].dropna()
            except KeyError:
                pass
    except Exception:
        pass

    missing_tickers = [t for t in tickers if t not in prices.index or pd.isna(prices.get(t))]

    if missing_tickers and market_type == "Indian" and target_date is None:
        clean_symbols = {t: t.replace('.NS', '').replace('.BO', '') for t in missing_tickers}
        still_missing = []
        try:
            import NseKit
            from concurrent.futures import ThreadPoolExecutor, as_completed
            nse = NseKit.Nse()
            
            def _fetch_nsekit_single(t_sym):
                t, sym = t_sym
                fetched = False
                price = None
                try:
                    if hasattr(nse, 'cm_live_equity_price_info'):
                        info = nse.cm_live_equity_price_info(sym)
                        if isinstance(info, dict) and 'LastTradedPrice' in info:
                            price = float(info['LastTradedPrice'])
                            fetched = True
                    if not fetched and hasattr(nse, 'cm_live_equity_info'):
                        info = nse.cm_live_equity_info(sym)
                        if isinstance(info, dict) and 'priceInfo' in info:
                            price = float(info['priceInfo'].get('lastPrice', 0))
                            fetched = True
                    if not fetched and hasattr(nse, 'equity_live_stock_info'):
                        info = nse.equity_live_stock_info(sym)
                        if isinstance(info, dict) and 'priceInfo' in info:
                            price = float(info['priceInfo'].get('lastPrice', 0))
                            fetched = True
                    if not fetched and hasattr(nse, 'get_quote'):
                        info = nse.get_quote(sym)
                        if isinstance(info, dict):
                            price = float(info.get('lastPrice', info.get('ltp', 0)))
                            fetched = True
                except Exception:
                    pass
                return t, sym, fetched, price

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(_fetch_nsekit_single, item): item for item in clean_symbols.items()}
                for future in as_completed(futures):
                    t, sym, fetched, price = future.result()
                    if fetched and price is not None:
                        prices[t] = price
                    else:
                        still_missing.append(t)
            clean_symbols = {t: clean_symbols[t] for t in still_missing}
        except ImportError:
            pass

        if clean_symbols:
            try:
                from bseindia import equity
                still_missing = []
                for t, sym in clean_symbols.items():
                    try:
                        fetched = False
                        if hasattr(equity, 'historical_stock_data'):
                            info = equity.historical_stock_data(sym, period='1D')
                            if info is not None and not info.empty:
                                prices[t] = float(info['Close'].iloc[-1])
                                fetched = True
                        if not fetched:
                            info = equity.stock_info(sym)
                            if isinstance(info, dict) and 'LTP' in info:
                                prices[t] = float(info['LTP'])
                                fetched = True
                        if not fetched:
                            still_missing.append(t)
                    except Exception:
                        still_missing.append(t)
                clean_symbols = {t: clean_symbols[t] for t in still_missing}
            except ImportError:
                pass
            
            if clean_symbols:
                try:
                    from bsedata.bse import BSE
                    bse = BSE(update_codes=False)
                    for t, sym in clean_symbols.items():
                        if sym.isdigit():
                            try:
                                q = bse.getQuote(sym)
                                prices[t] = float(q['currentValue'])
                            except Exception:
                                pass
                except ImportError:
                    pass

    return prices


def process_portfolio_file(uploaded_file, market_type, target_date_arg):
    try:
        if uploaded_file.name.endswith('.csv'):
            portfolio_df = pd.read_csv(uploaded_file)
        else:
            portfolio_df = pd.read_excel(uploaded_file)
        
        required_cols = ['symbol', 'units', 'value']
        lower_cols = [col.strip().lower() for col in portfolio_df.columns]
        
        if not all(col in lower_cols for col in required_cols):
            return None, f"File {uploaded_file.name} must contain the following columns: {', '.join(required_cols)}"
        
        portfolio_df.columns = [col.strip().lower() for col in portfolio_df.columns]
        portfolio = portfolio_df[['symbol', 'units', 'value']].copy()
        portfolio.rename(columns={'value': 'original_value'}, inplace=True)
        
        portfolio['units'] = pd.to_numeric(portfolio['units'].astype(str).str.replace(',', ''), errors='coerce')
        portfolio['original_value'] = pd.to_numeric(portfolio['original_value'].astype(str).str.replace(',', ''), errors='coerce')
        portfolio.dropna(subset=['units', 'original_value'], inplace=True)
        
        if market_type == "Indian":
            portfolio['ticker'] = portfolio['symbol'].astype(str).apply(
                lambda x: x if str(x).upper().endswith('.NS') or str(x).upper().endswith('.BO') else str(x) + ".NS"
            )
        else:
            portfolio['ticker'] = portfolio['symbol'].astype(str)
        
        tickers = portfolio['ticker'].tolist()
        
        latest_prices = fetch_prices(tickers, target_date_arg, market_type)
        
        if latest_prices.empty:
            return None, f"Could not fetch any data for {uploaded_file.name}."
            
        portfolio['latest_price'] = portfolio['ticker'].map(latest_prices)
        failed_fetches = portfolio[portfolio['latest_price'].isna()]['symbol'].tolist()
        
        if failed_fetches:
            st.warning(f"Could not fetch data for {uploaded_file.name}: {', '.join(failed_fetches)}. Excluded.")
            portfolio.dropna(subset=['latest_price'], inplace=True)

        if not portfolio.empty:
            portfolio['current_value'] = portfolio['latest_price'] * portfolio['units']
            portfolio['return_$'] = portfolio['current_value'] - portfolio['original_value']
            portfolio['return_%'] = 0.0
            mask = portfolio['original_value'] != 0
            portfolio.loc[mask, 'return_%'] = (portfolio.loc[mask, 'return_$'] / portfolio.loc[mask, 'original_value']) * 100
            return portfolio, None
        else:
            return None, f"No valid data to display for {uploaded_file.name} after fetching prices."
            
    except Exception as e:
        return None, f"An error occurred for {uploaded_file.name}: {e}"


def get_macro_metrics(results_df, date_label):
    total_original_value = results_df['original_value'].sum()
    total_current_value = results_df['current_value'].sum()
    total_return_dollar = results_df['return_$'].sum()
    total_return_percent = (total_return_dollar / total_original_value) * 100 if total_original_value != 0 else 0.0
    pl_class = "success" if total_return_dollar > 0 else "danger" if total_return_dollar < 0 else "neutral"

    return [
        {"label": "Original", "value": f"{total_original_value:,.2f}", "delta": "Capital Deployed", "kind": "primary"},
        {"label": f"Valuation", "value": f"{total_current_value:,.2f}", "delta": f"As of {date_label}", "kind": "info"},
        {"label": "Total P/L", "value": f"{total_return_percent:,.2f}%", "delta": f"{total_return_dollar:,.2f}", "kind": pl_class},
        {"label": "Positions", "value": str(len(results_df)), "delta": "Active holdings", "kind": "neutral"},
    ]


def render_portfolio_tables(results_df):
    display_df = results_df[['symbol', 'units', 'original_value', 'latest_price', 'current_value', 'return_$', 'return_%']].copy()
    display_df = display_df.rename(columns={'symbol': 'Symbol', 'units': 'Units', 'original_value': 'Orig Val', 'latest_price': 'Price', 'current_value': 'Curr Val', 'return_$': 'P/L', 'return_%': 'P/L (%)'})
    
    st.dataframe(
        display_df.style.format({
            'Orig Val': '{:,.2f}', 
            'Price': '{:,.2f}', 
            'Curr Val': '{:,.2f}', 
            'P/L': '{:,.2f}', 
            'P/L (%)': '{:,.2f}%', 
            'Units': '{:,.2f}'
        }).background_gradient(cmap='RdYlGn', subset=['P/L (%)'], vmin=-10, vmax=10), 
        use_container_width=True, 
        height=400
    )

def render_portfolio_charts(results_df, prefix=""):
    fig_bar = px.bar(results_df, x='symbol', y='return_%', color='return_%', color_continuous_scale='RdYlGn', title=f'{prefix} Return %')
    theme.apply_chart_theme(fig_bar)
    st.plotly_chart(fig_bar, use_container_width=True)


# --- Sidebar Controls ---
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1rem 0; margin-bottom:1rem;">
        <div style="font-size:1.75rem; font-weight:800; color:var(--amber); font-family:var(--display); letter-spacing:1px;">RETURNS</div>
        <div style="color:var(--ink-secondary); font-size:0.75rem; margin-top:0.25rem; font-weight:500;">Portfolio Returns Tracker</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="sidebar-title" style="color:var(--amber); font-family:var(--display); text-transform:uppercase; font-size:0.8rem; font-weight:700; margin-bottom:1rem;">⚙️ App Mode</div>', unsafe_allow_html=True)
    app_mode = st.radio("Select Mode", ("Single Portfolio", "Compare Portfolios"), label_visibility="collapsed")
    st.session_state.app_mode = app_mode

    st.divider()

    st.markdown('<div class="sidebar-title" style="color:var(--amber); font-family:var(--display); text-transform:uppercase; font-size:0.8rem; font-weight:700; margin-bottom:1rem;">📂 Data Input</div>', unsafe_allow_html=True)
    if app_mode == "Single Portfolio":
        uploaded_file = st.file_uploader("Upload Portfolio File", type=["csv", "xlsx", "xls"], key="single_up", help="Must contain 'symbol', 'units', and 'value'")
    else:
        uploaded_file_1 = st.file_uploader("Upload Portfolio 1", type=["csv", "xlsx", "xls"], key="comp1_up")
        uploaded_file_2 = st.file_uploader("Upload Portfolio 2", type=["csv", "xlsx", "xls"], key="comp2_up")

    st.markdown('<div class="sidebar-title" style="color:var(--amber); font-family:var(--display); text-transform:uppercase; font-size:0.8rem; font-weight:700; margin-bottom:1rem; margin-top:1rem;">🌍 Market Settings</div>', unsafe_allow_html=True)
    market_type = st.radio("Select Market Type", ("Global", "Indian"), label_visibility="collapsed")

    st.divider()

    st.markdown('<div class="sidebar-title" style="color:var(--amber); font-family:var(--display); text-transform:uppercase; font-size:0.8rem; font-weight:700; margin-bottom:1rem;">📅 Valuation Date</div>', unsafe_allow_html=True)
    date_mode = st.radio("Valuation Mode", ["Live / Latest", "Historical Date"], label_visibility="collapsed")

    selected_valuation_date = None
    if date_mode == "Historical Date":
        selected_valuation_date = st.date_input("Select Date", value=datetime.today() - timedelta(days=1), max_value=datetime.today())

    st.divider()

    run_button = st.button("Fetch Valuations", use_container_width=True, type="primary")
    status_placeholder = st.empty()

    st.divider()
    st.markdown(f"""
    <div style='padding:1rem; text-align:center;'>
        <p style='font-size:0.75rem; margin:0; color:var(--ink-secondary); font-family:var(--data);'>
            <strong>Version:</strong> {VERSION}<br>
            <strong>Engine:</strong> Multi-Source API
        </p>
    </div>
    """, unsafe_allow_html=True)


# --- Main Application Logic ---
components.render_header("RETURNS", "Real-time valuation and performance tracking engine")

if run_button:
    target_date_arg = selected_valuation_date if date_mode == "Historical Date" else None
    date_display = str(target_date_arg) if target_date_arg else "Latest Live"

    if app_mode == "Single Portfolio":
        if uploaded_file is not None:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                portfolio, err = process_portfolio_file(uploaded_file, market_type, target_date_arg)
                if err:
                    st.error(err)
                    st.session_state.data_loaded_single = False
                else:
                    st.session_state.results_single = portfolio
                    st.session_state.data_loaded_single = True
                    st.session_state.valuation_date_label = date_display
                    status_placeholder.success(f"✅ Update Complete!")
        else:
            components.render_warning_box("Missing Input", "Please upload a file.")

    elif app_mode == "Compare Portfolios":
        if uploaded_file_1 is not None and uploaded_file_2 is not None:
            with st.spinner("Processing both portfolios..."):
                p1, err1 = process_portfolio_file(uploaded_file_1, market_type, target_date_arg)
                p2, err2 = process_portfolio_file(uploaded_file_2, market_type, target_date_arg)
                
                if err1 or err2:
                    if err1: components.render_warning_box("Error", err1)
                    if err2: components.render_warning_box("Error", err2)
                    st.session_state.data_loaded_comp = False
                else:
                    st.session_state.results_comp_1 = p1
                    st.session_state.results_comp_2 = p2
                    st.session_state.comp_names = (uploaded_file_1.name, uploaded_file_2.name)
                    st.session_state.data_loaded_comp = True
                    st.session_state.valuation_date_label = date_display
                    status_placeholder.success(f"✅ Comparison Ready!")
        else:
            components.render_warning_box("Missing Input", "Please upload two files to compare.")


# --- Display Results ---
if st.session_state.app_mode == "Single Portfolio":
    if st.session_state.data_loaded_single:
        results_df = st.session_state.results_single
        date_label = st.session_state.valuation_date_label

        # Top-Level Macro View (Matches Swing Dashboard Structure)
        metrics = get_macro_metrics(results_df, date_label)
        components.render_metric_row(metrics)

        # Tabulated Hierarchy
        st.markdown("<br>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Performance Snapshot", "Detailed Holdings"])
        
        with tab1:
            components.render_section_header("Visual Analytics", "Portfolio allocation and performance returns", icon="chart", accent="emerald")
            render_portfolio_charts(results_df)

        with tab2:
            components.render_section_header("Symbol Level Returns", "Data breakdown and detailed metrics", icon="database", accent="cyan")
            render_portfolio_tables(results_df)
            
            buf = io.BytesIO()
            results_df.to_csv(buf, index=False, encoding="utf-8-sig")
            st.download_button("Download CSV", data=buf.getvalue(), file_name="returns_single.csv", mime="text/csv", use_container_width=True)

    else:
        components.render_info_box("Welcome", "Upload a CSV/Excel file, select settings, and fetch valuations.", color="cyan")

elif st.session_state.app_mode == "Compare Portfolios":
    if st.session_state.data_loaded_comp:
        r1 = st.session_state.results_comp_1
        r2 = st.session_state.results_comp_2
        n1, n2 = st.session_state.comp_names
        date_label = st.session_state.valuation_date_label

        # 1. Macro Metrics Interleaved Section
        components.render_section_header("Macro Comparison", "Top-level portfolio summary metrics", icon="activity", accent="amber")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<h3 style='text-align:center; color:var(--amber); font-family:var(--display); padding-bottom:1rem;'>{n1}</h3>", unsafe_allow_html=True)
            m1 = get_macro_metrics(r1, date_label)
            # Create a 2x2 grid for the 4 metrics using render_metric_row
            components.render_metric_row([m1[0], m1[1]])
            components.render_metric_row([m1[2], m1[3]])
                
        with col2:
            st.markdown(f"<h3 style='text-align:center; color:var(--cyan); font-family:var(--display); padding-bottom:1rem;'>{n2}</h3>", unsafe_allow_html=True)
            m2 = get_macro_metrics(r2, date_label)
            # Create a 2x2 grid for the 4 metrics using render_metric_row
            components.render_metric_row([m2[0], m2[1]])
            components.render_metric_row([m2[2], m2[3]])

        # 2. Tabular Data Interleaved Section
        components.render_section_header("Holdings Comparison", "Side-by-side data table breakdown", icon="grid", accent="emerald")
        tc1, tc2 = st.columns(2)
        with tc1:
            render_portfolio_tables(r1)
        with tc2:
            render_portfolio_tables(r2)

        # 3. Visual Charts Interleaved Section
        components.render_section_header("Performance Comparison", "Visual analytics on return metrics", icon="chart", accent="cyan")
        cc1, cc2 = st.columns(2)
        with cc1:
            render_portfolio_charts(r1, prefix=f"{n1}")
        with cc2:
            render_portfolio_charts(r2, prefix=f"{n2}")

    else:
        components.render_info_box("Compare Mode", "Upload two different portfolio CSVs to compare them side-by-side.", color="amber")

# --- Footer ---
st.divider()
ist = timezone(offset=timedelta(hours=5, minutes=30))
now_ist = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")
st.markdown(f"""
<div style="text-align:center; padding:1rem 0; color:var(--ink-tertiary); font-size:0.75rem; font-family:var(--data);">
    <span>© 2026 Hemrek Capital</span>
    <span style="margin:0 0.5rem; color:var(--border-subtle);">|</span>
    <span>{VERSION}</span>
    <span style="margin:0 0.5rem; color:var(--border-subtle);">|</span>
    <span>{now_ist}</span>
</div>
""", unsafe_allow_html=True)