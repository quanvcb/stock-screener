"""
GIAO DIỆN WEB DASHBOARD THEO DÕI BỘ LỌC CỔ PHIẾU TRADINGVIEW THỜI GIAN THỰC
Chạy lệnh: streamlit run tv_dashboard_web.py
"""

import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="TradingView VN-Index Screener (1W)",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tùy chỉnh CSS giao diện chuyên nghiệp
st.markdown("""
<style>
    .main-header {
        font-size: 24px;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 4px;
    }
    .sub-header {
        font-size: 13px;
        color: #666;
        margin-bottom: 16px;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def rating_to_text(val):
    if val is None:
        return "N/A"
    if val >= 0.5:
        return "Mua mạnh"
    elif val > 0.1:
        return "Mua"
    elif val <= -0.5:
        return "Bán mạnh"
    elif val < -0.1:
        return "Bán"
    else:
        return "Trung tính"

# Khởi tạo session TradingView
@st.cache_resource
def get_tv_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://vn.tradingview.com/"
    })
    login_url = "https://www.tradingview.com/accounts/signin/"
    payload = {
        "username": "quanvcb@gmail.com",
        "password": "Quochien@2021",
        "remember": "true"
    }
    try:
        r = session.post(login_url, data=payload, timeout=10)
        if r.status_code == 200 and not r.json().get("error"):
            return session, "quan357 (Đã kết nối)"
    except Exception:
        pass
    return session, "Khách (Chế độ công khai)"

# Hàm lấy dữ liệu bộ lọc TradingView Scanner API
def fetch_screener_data(session):
    scan_url = "https://scanner.tradingview.com/vietnam/scan"
    payload = {
        "filter": [
            {"left": "exchange", "operation": "equal", "right": "HOSE"},
            {"left": "type", "operation": "equal", "right": "stock"},
            # Lọc theo MACD Tuần (1W) cắt lên Signal
            {"left": "MACD.macd|1W", "operation": "crosses_above", "right": "MACD.signal|1W"}
        ],
        "options": {"lang": "vi"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name",                 # 0: Mã CP
            "description",          # 1: Tên doanh nghiệp
            "close",                # 2: Giá đóng cửa
            "change",               # 3: % Thay đổi
            "volume",               # 4: Khối lượng
            "MACD.macd|1W",         # 5: MACD Tuần
            "MACD.signal|1W",       # 6: Signal Tuần
            "MACD.hist|1W",         # 7: Histogram Tuần
            "RSI",                  # 8: RSI (theo chuẩn bộ lọc TradingView Screener)
            "Recommend.All",        # 9: Xếp hạng kỹ thuật tổng hợp chuẩn TradingView
            "Recommend.MA",         # 10: Đánh giá MA
            "Recommend.Other"       # 11: Đánh giá Dao động
        ],
        "range": [0, 200]
    }

    try:
        res = session.post(scan_url, json=payload, timeout=15)
        if res.status_code == 200:
            data = res.json()
            items = data.get("data", [])
            records = []
            for item in items:
                d = item.get("d", [])
                if len(d) < 12:
                    continue
                sym = d[0]
                desc = d[1]
                close = d[2]
                change = round(d[3], 2) if d[3] is not None else 0.0
                vol = int(d[4]) if d[4] is not None else 0
                macd = round(d[5], 2) if d[5] is not None else 0.0
                signal = round(d[6], 2) if d[6] is not None else 0.0
                hist = round(d[7], 2) if d[7] is not None else round(macd - signal, 2)
                rsi = round(d[8], 2) if d[8] is not None else 0.0
                
                # Xếp hạng tổng thể
                rec_all = rating_to_text(d[9])
                if "Mua mạnh" in rec_all:
                    rec_badge = "🟢 Mua mạnh"
                elif "Mua" in rec_all:
                    rec_badge = "🟢 Mua"
                elif "Bán mạnh" in rec_all:
                    rec_badge = "🔴 Bán mạnh"
                elif "Bán" in rec_all:
                    rec_badge = "🔴 Bán"
                else:
                    rec_badge = "🟡 Trung tính"

                # Đánh giá MA / Dao động
                rec_ma = rating_to_text(d[10])
                rec_osc = rating_to_text(d[11])
                ma_osc_str = f"MA: {rec_ma}, Dao động: {rec_osc}"

                tv_url = f"https://vn.tradingview.com/chart/xKsA49eB/?symbol=HOSE:{sym}"
                
                records.append({
                    "Mã CP": sym,
                    "Xếp hạng kỹ thuật": rec_badge,
                    "Đánh giá MA / Dao động": ma_osc_str,
                    "RSI": rsi,
                    "Giá (đ)": close,
                    "Thay đổi (%)": change,
                    "Khối lượng": vol,
                    "MACD (1W)": macd,
                    "Signal (1W)": signal,
                    "Histogram": hist,
                    "Tên Doanh Nghiệp": desc,
                    "Xem Biểu đồ TV": tv_url
                })
            return pd.DataFrame(records)
    except Exception as e:
        st.error(f"Lỗi truy vấn TradingView: {e}")
    return pd.DataFrame()

# Khởi tạo Session
session, auth_status = get_tv_session()

# Sidebar điều khiển
with st.sidebar:
    st.image("https://vn.tradingview.com/static/images/logo.svg", width=150)
    st.markdown("### ⚙️ Cấu Hình Bộ Lọc")
    st.markdown(f"**Tài khoản:** `{auth_status}`")
    st.markdown(f"**Bố cục biểu đồ:** `LuxAlgo & MACD CMF`")
    
    st.markdown("---")
    auto_refresh = st.checkbox("🔄 Tự động cập nhật (Realtime)", value=False)
    refresh_rate = st.selectbox("Tần suất làm mới", [10, 30, 60, 120], index=1, format_func=lambda x: f"{x} giây")
    
    min_vol = st.number_input("Khối lượng tối thiểu (CP):", min_value=0, value=0, step=5000)
    search_sym = st.text_input("🔍 Tìm nhanh mã CP:").upper().strip()
    
    if st.button("🚀 Quét Lại Ngay", use_container_width=True):
        st.rerun()

# Tiêu đề giao diện
st.markdown('<div class="main-header">📈 BỘ LỌC CỔ PHIẾU REALTIME - TRADINGVIEW</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">Tiêu chí: <b>HOSE (VN-Index) | Đồ thị Tuần (1W) | MACD Xanh Cắt Lên Signal Cam | Histogram Đổi Màu</b> • Cập nhật: <b>{datetime.now().strftime("%H:%M:%S - %d/%m/%Y")}</b></div>', unsafe_allow_html=True)

# Lấy dữ liệu
df_stocks = fetch_screener_data(session)

if df_stocks.empty:
    st.warning("⚠️ Hiện tại không lấy được danh sách hoặc không có mã nào thỏa mãn điều kiện.")
else:
    # Lọc theo thanh khoản và tìm kiếm
    if min_vol > 0:
        df_stocks = df_stocks[df_stocks["Khối lượng"] >= min_vol]
    if search_sym:
        df_stocks = df_stocks[df_stocks["Mã CP"].str.contains(search_sym)]

    # Sắp xếp theo Xếp hạng kỹ thuật: Mua mạnh -> Mua -> Trung tính -> Bán -> Bán mạnh
    rank_map = {
        "🟢 Mua mạnh": 1,
        "🟢 Mua": 2,
        "🟡 Trung tính": 3,
        "🔴 Bán": 4,
        "🔴 Bán mạnh": 5
    }
    df_stocks["_rank"] = df_stocks["Xếp hạng kỹ thuật"].map(lambda x: rank_map.get(x, 99))
    df_stocks = df_stocks.sort_values(by=["_rank", "RSI"], ascending=[True, False]).drop(columns=["_rank"]).reset_index(drop=True)

    # Thống kê nhanh Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng Số Cổ Phiếu Đạt", f"{len(df_stocks)} mã")
    with col2:
        up_count = len(df_stocks[df_stocks["Xếp hạng kỹ thuật"].str.contains("Mua")])
        st.metric("Số Mã Đạt Xếp Hạng MUA", f"{up_count} mã", delta=f"{up_count}/{len(df_stocks)}")
    with col3:
        rsi_bull = len(df_stocks[df_stocks["RSI"] >= 50])
        st.metric("RSI Mạnh (≥ 50)", f"{rsi_bull} mã")
    with col4:
        top_vol = df_stocks.sort_values(by="Khối lượng", ascending=False).iloc[0]["Mã CP"] if not df_stocks.empty else "N/A"
        st.metric("Thanh Khoản Lớn Nhất", top_vol)

    st.markdown("---")

    # Thứ tự các cột rõ ràng theo đúng yêu cầu
    col_order = [
        "Mã CP",
        "Xếp hạng kỹ thuật",
        "Đánh giá MA / Dao động",
        "RSI",
        "Giá (đ)",
        "Thay đổi (%)",
        "Khối lượng",
        "MACD (1W)",
        "Signal (1W)",
        "Histogram",
        "Xem Biểu đồ TV",
        "Tên Doanh Nghiệp"
    ]

    st.dataframe(
        df_stocks,
        column_order=col_order,
        column_config={
            "Mã CP": st.column_config.TextColumn("Mã CP", width=80),
            "Xếp hạng kỹ thuật": st.column_config.TextColumn("Xếp hạng kỹ thuật", width=120),
            "Đánh giá MA / Dao động": st.column_config.TextColumn("Đánh giá MA / Dao động", width=220),
            "RSI": st.column_config.NumberColumn("RSI", format="%.2f", width=85),
            "Giá (đ)": st.column_config.NumberColumn("Giá (đ)", format="%d đ", width=95),
            "Thay đổi (%)": st.column_config.NumberColumn("Thay đổi (%)", format="%.2f %%", width=100),
            "Khối lượng": st.column_config.NumberColumn("Khối lượng", format="%d CP", width=110),
            "MACD (1W)": st.column_config.NumberColumn("MACD (1W)", format="%.2f", width=95),
            "Signal (1W)": st.column_config.NumberColumn("Signal (1W)", format="%.2f", width=95),
            "Histogram": st.column_config.NumberColumn("Histogram", format="%.2f", width=95),
            "Xem Biểu đồ TV": st.column_config.LinkColumn("Xem Biểu Đồ TradingView", display_text="📊 Mở TV", width=100),
            "Tên Doanh Nghiệp": st.column_config.TextColumn("Tên Doanh Nghiệp", width=220)
        },
        use_container_width=True,
        hide_index=True
    )

    # Nút mở nhanh biểu đồ dạng grid
    st.markdown("### 🎯 Phím Tắt Mở Trực Tiếp Trên TradingView (Bố Cục LuxAlgo & MACD+CMF):")
    ticker_cols = st.columns(8)
    for idx, row in df_stocks.iterrows():
        col_idx = idx % 8
        with ticker_cols[col_idx]:
            sym = row["Mã CP"]
            url = row["Xem Biểu đồ TV"]
            st.link_button(f"📊 {sym}", url, use_container_width=True)

# Tự động refresh nếu được bật
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
