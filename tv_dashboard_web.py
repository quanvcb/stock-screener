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
    page_title="TradingView VN-Index Screener (Đa Khung Thời Gian)",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tùy chỉnh CSS giao diện chuyên nghiệp và tối ưu cho mobile
st.markdown("""
<style>
    .main-header {
        font-size: 22px;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 4px;
    }
    .sub-header {
        font-size: 13px;
        color: #555;
        margin-bottom: 14px;
        line-height: 1.5;
    }
    .block-container {
        padding-top: 1.2rem;
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

def get_hist_color_4c(h, h_prev):
    """
    Xác định màu sắc của thanh Histogram theo quy tắc MACD 4 màu (4C):
    - Histogram >= 0: Xanh đậm (tăng), Xanh nhạt (giảm)
    - Histogram < 0: Đỏ đậm (giảm), Đỏ nhạt (tăng/co lại)
    """
    if h is None or h_prev is None:
        return "N/A"
    if h >= 0:
        return "Xanh đậm" if h >= h_prev else "Xanh nhạt"
    else:
        return "Đỏ đậm" if h <= h_prev else "Đỏ nhạt"

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

# Hàm lấy dữ liệu bộ lọc TradingView Scanner API đa điều kiện
def fetch_screener_data(session):
    scan_url = "https://scanner.tradingview.com/vietnam/scan"
    payload = {
        "filter": [
            {"left": "exchange", "operation": "equal", "right": "HOSE"},
            {"left": "type", "operation": "equal", "right": "stock"}
        ],
        "options": {"lang": "vi"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name",                     # 0: Mã cổ phiếu
            "description",              # 1: Tên doanh nghiệp
            "close",                    # 2: Giá đóng cửa
            "change",                   # 3: % Thay đổi
            "volume",                   # 4: Khối lượng
            "MACD.macd",                # 5: MACD Ngày (1D)
            "MACD.signal",              # 6: Signal Ngày (1D)
            "MACD.hist",                # 7: Histogram Ngày (1D)
            "MACD.macd[1]",             # 8: MACD Ngày nến trước [1]
            "MACD.signal[1]",           # 9: Signal Ngày nến trước [1]
            "MACD.hist[1]",             # 10: Histogram Ngày nến trước [1]
            "MACD.macd[2]",             # 11: MACD Ngày nến [2]
            "MACD.signal[2]",           # 12: Signal Ngày nến [2]
            "MACD.hist[2]",             # 13: Histogram Ngày nến [2]
            "MACD.macd|1W",             # 14: MACD Tuần (1W)
            "MACD.signal|1W",           # 15: Signal Tuần (1W)
            "MACD.hist|1W",             # 16: Histogram Tuần (1W)
            "MACD.macd[1]|1W",          # 17: MACD Tuần nến trước [1]
            "MACD.signal[1]|1W",        # 18: Signal Tuần nến trước [1]
            "MACD.hist[1]|1W",          # 19: Histogram Tuần nến trước [1]
            "RSI",                      # 20: RSI
            "Recommend.All",            # 21: Xếp hạng kỹ thuật tổng hợp
            "Recommend.MA",             # 22: Đánh giá MA
            "Recommend.Other"           # 23: Đánh giá Dao động
        ],
        "range": [0, 500]
    }

    try:
        res = session.post(scan_url, json=payload, timeout=20)
        if res.status_code == 200:
            data = res.json()
            items = data.get("data", [])
            records = []
            for item in items:
                d = item.get("d", [])
                if len(d) < 24:
                    continue

                sym = d[0]
                desc = d[1]
                close = d[2]
                change = round(d[3], 2) if d[3] is not None else 0.0
                vol = int(d[4]) if d[4] is not None else 0

                m_d, s_d, h_d = d[5], d[6], d[7]
                m_d1, s_d1, h_d1 = d[8], d[9], d[10]
                m_d2, s_d2, h_d2 = d[11], d[12], d[13]

                m_w, s_w, h_w = d[14], d[15], d[16]
                m_w1, s_w1, h_w1 = d[17], d[18], d[19]

                rsi = round(d[20], 2) if d[20] is not None else 0.0

                # 1. KIỂM TRA ĐIỀU KIỆN 1 (ĐIỀU KIỆN CŨ / CÒN LẠI):
                # Khung Tuần (1W): MACD cắt lên Signal (crosses_above)
                cond_old = False
                if m_w is not None and s_w is not None and m_w1 is not None and s_w1 is not None:
                    if m_w1 <= s_w1 and m_w > s_w:
                        cond_old = True

                # 2. KIỂM TRA ĐIỀU KIỆN 2 (ĐIỀU KIỆN MỚI):
                # - Khung Tuần (1W):
                #   + Đường xanh hướng lên: m_w > m_w1
                #   + Nằm trên đường cam: m_w > s_w
                #   + Histogram tuần đổi màu: h_w1 <= 0 và h_w > 0 HOẶC h_w > h_w1
                # - Khung Ngày (1D):
                #   + MACD Histogram đổi màu (color_d != color_d1)
                #   + Đường xanh hướng lên đường cam (m_d > m_d1 và h_d > h_d1)
                cond_new = False
                day_detail = ""
                if (m_w is not None and m_w1 is not None and s_w is not None and h_w is not None and h_w1 is not None):
                    week_green_up = (m_w > m_w1)
                    week_above_cam = (m_w > s_w)
                    week_hist_change = ((h_w1 <= 0 and h_w > 0) or (h_w > h_w1))

                    if week_green_up and week_above_cam and week_hist_change:
                        if (m_d is not None and m_d1 is not None and s_d is not None and 
                            h_d is not None and h_d1 is not None and h_d2 is not None):
                            c_d = get_hist_color_4c(h_d, h_d1)
                            c_d1 = get_hist_color_4c(h_d1, h_d2)
                            day_hist_change = (c_d != c_d1 and c_d in ["Đỏ nhạt", "Xanh đậm"])
                            day_green_up = (m_d > m_d1)

                            if day_hist_change and day_green_up:
                                cond_new = True
                                if m_d <= s_d:
                                    day_detail = f"{c_d1} ➔ {c_d} (Dưới cam)"
                                else:
                                    day_detail = f"{c_d1} ➔ {c_d} (Trên cam)"

                # Phân loại ngắn gọn vào cột 'ĐK Lọc' (tối ưu hiển thị điện thoại)
                if cond_old and cond_new:
                    filter_cond_badge = "🟢 Cả 2 ĐK"
                    filter_cond_key = "both"
                elif cond_new:
                    filter_cond_badge = "🔵 ĐK mới"
                    filter_cond_key = "new"
                elif cond_old:
                    filter_cond_badge = "🟠 ĐK cũ"
                    filter_cond_key = "old"
                else:
                    continue  # Không thỏa mãn điều kiện nào thì bỏ qua

                # Xếp hạng tổng thể
                rec_all = rating_to_text(d[21])
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
                rec_ma = rating_to_text(d[22])
                rec_osc = rating_to_text(d[23])
                ma_osc_str = f"MA: {rec_ma}, Dao động: {rec_osc}"

                tv_url = f"https://vn.tradingview.com/chart/xKsA49eB/?symbol=HOSE:{sym}"
                
                records.append({
                    "Mã CP": sym,
                    "ĐK Lọc": filter_cond_badge,
                    "cond_key": filter_cond_key,
                    "Xếp hạng kỹ thuật": rec_badge,
                    "Đánh giá MA / Dao động": ma_osc_str,
                    "Xem Biểu đồ TV": tv_url,
                    "Giá (đ)": close,
                    "Thay đổi (%)": change,
                    "Khối lượng": vol,
                    "MACD (1W)": round(m_w, 2) if m_w is not None else 0.0,
                    "Signal (1W)": round(s_w, 2) if s_w is not None else 0.0,
                    "Histogram (1W)": round(h_w, 2) if h_w is not None else 0.0,
                    "MACD (1D)": round(m_d, 2) if m_d is not None else 0.0,
                    "Signal (1D)": round(s_d, 2) if s_d is not None else 0.0,
                    "Histogram (1D)": round(h_d, 2) if h_d is not None else 0.0,
                    "Chi tiết Ngày": day_detail if day_detail else "Tuần cắt lên",
                    "RSI": rsi,
                    "Tên Doanh Nghiệp": desc
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
    
    cond_filter_opt = st.selectbox(
        "🎯 Lọc theo điều kiện:",
        [
            "Tất cả", 
            "Chỉ ĐK mới (Tuần MACD > Cam, Ngày hướng lên)", 
            "Chỉ ĐK cũ (Tuần MACD cắt lên Cam)", 
            "Chỉ Cả 2 ĐK"
        ],
        index=0
    )

    auto_refresh = st.checkbox("🔄 Tự động cập nhật (Realtime)", value=False)
    refresh_rate = st.selectbox("Tần suất làm mới", [10, 30, 60, 120], index=1, format_func=lambda x: f"{x} giây")
    
    min_vol = st.number_input("Khối lượng tối thiểu (CP):", min_value=0, value=0, step=5000)
    search_sym = st.text_input("🔍 Tìm nhanh mã CP:").upper().strip()
    
    if st.button("🚀 Quét Lại Ngay", use_container_width=True):
        st.rerun()

# Tiêu đề giao diện
st.markdown('<div class="main-header">📈 BỘ LỌC CỔ PHIẾU REALTIME - TRADINGVIEW</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="sub-header">
    • <b>[ĐK MỚI]:</b> Tuần (1W) MACD Xanh hướng lên & nằm trên Signal Cam, Histogram đổi màu | Ngày (1D) Histogram đổi màu, MACD Xanh hướng lên Signal Cam.<br>
    • <b>[ĐK CŨ]:</b> Tuần (1W) MACD Xanh cắt lên Signal Cam.<br>
    • Cập nhật: <b>{datetime.now().strftime("%H:%M:%S - %d/%m/%Y")}</b>
</div>
""", unsafe_allow_html=True)

# Lấy dữ liệu
df_stocks = fetch_screener_data(session)

if df_stocks.empty:
    st.warning("⚠️ Hiện tại không lấy được danh sách hoặc không có mã nào thỏa mãn điều kiện.")
else:
    # Lọc theo bộ chọn điều kiện sidebar
    if "Chỉ ĐK mới" in cond_filter_opt:
        df_stocks = df_stocks[df_stocks["cond_key"].isin(["new", "both"])]
    elif "Chỉ ĐK cũ" in cond_filter_opt:
        df_stocks = df_stocks[df_stocks["cond_key"].isin(["old", "both"])]
    elif "Chỉ Cả 2 ĐK" in cond_filter_opt:
        df_stocks = df_stocks[df_stocks["cond_key"] == "both"]

    # Lọc theo thanh khoản và tìm kiếm
    if min_vol > 0:
        df_stocks = df_stocks[df_stocks["Khối lượng"] >= min_vol]
    if search_sym:
        df_stocks = df_stocks[df_stocks["Mã CP"].str.contains(search_sym)]

    # SẮP XẾP CỔ PHIẾU THEO THỨ TỰ:
    # 1. Điều kiện lọc: Cả 2 ĐK (1) -> ĐK mới (2) -> ĐK cũ (3)
    # 2. Xếp hạng kỹ thuật: Mua mạnh (1) -> Mua (2) -> Trung tính (3) -> Bán (4) -> Bán mạnh (5)
    # 3. RSI giảm dần
    cond_sort_map = {
        "both": 1,
        "new": 2,
        "old": 3
    }
    rank_map = {
        "🟢 Mua mạnh": 1,
        "🟢 Mua": 2,
        "🟡 Trung tính": 3,
        "🔴 Bán": 4,
        "🔴 Bán mạnh": 5
    }
    df_stocks["_cond_order"] = df_stocks["cond_key"].map(lambda x: cond_sort_map.get(x, 99))
    df_stocks["_rank"] = df_stocks["Xếp hạng kỹ thuật"].map(lambda x: rank_map.get(x, 99))
    df_stocks = df_stocks.sort_values(by=["_cond_order", "_rank", "RSI"], ascending=[True, True, False]).drop(columns=["_cond_order", "_rank", "cond_key"]).reset_index(drop=True)

    # Thống kê nhanh Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng Số Cổ Phiếu Đạt", f"{len(df_stocks)} mã")
    with col2:
        both_count = len(df_stocks[df_stocks["ĐK Lọc"].str.contains("Cả 2")])
        st.metric("🟢 Cả 2 ĐK", f"{both_count} mã")
    with col3:
        new_count = len(df_stocks[df_stocks["ĐK Lọc"].str.contains("ĐK mới|Cả 2")])
        st.metric("🔵 ĐK Mới", f"{new_count} mã")
    with col4:
        old_count = len(df_stocks[df_stocks["ĐK Lọc"].str.contains("ĐK cũ|Cả 2")])
        st.metric("🟠 ĐK Cũ", f"{old_count} mã")

    st.markdown("---")

    # Thứ tự các cột hiển thị trong bảng:
    # Cột 'Đánh giá MA / Dao động' và 'Xem Biểu đồ TV' được chuyển ra SAU 'Xếp hạng kỹ thuật'
    col_order = [
        "Mã CP",
        "ĐK Lọc",
        "Xếp hạng kỹ thuật",
        "Đánh giá MA / Dao động",
        "Xem Biểu đồ TV",
        "Giá (đ)",
        "Thay đổi (%)",
        "Khối lượng",
        "MACD (1W)",
        "Signal (1W)",
        "Histogram (1W)",
        "MACD (1D)",
        "Signal (1D)",
        "Chi tiết Ngày",
        "RSI",
        "Tên Doanh Nghiệp"
    ]

    st.dataframe(
        df_stocks,
        column_order=col_order,
        column_config={
            "Mã CP": st.column_config.TextColumn("Mã CP", width=75),
            "ĐK Lọc": st.column_config.TextColumn("ĐK Lọc", width=95),
            "Xếp hạng kỹ thuật": st.column_config.TextColumn("Xếp hạng kỹ thuật", width=125),
            "Đánh giá MA / Dao động": st.column_config.TextColumn("Đánh giá MA / Dao động", width=190),
            "Xem Biểu đồ TV": st.column_config.LinkColumn("TradingView", display_text="📊 Mở TV", width=95),
            "Giá (đ)": st.column_config.NumberColumn("Giá (đ)", format="%d đ", width=90),
            "Thay đổi (%)": st.column_config.NumberColumn("Thay đổi (%)", format="%.2f %%", width=95),
            "Khối lượng": st.column_config.NumberColumn("Khối lượng", format="%d CP", width=105),
            "MACD (1W)": st.column_config.NumberColumn("MACD (1W)", format="%.2f", width=90),
            "Signal (1W)": st.column_config.NumberColumn("Signal (1W)", format="%.2f", width=90),
            "Histogram (1W)": st.column_config.NumberColumn("Histogram (1W)", format="%.2f", width=95),
            "MACD (1D)": st.column_config.NumberColumn("MACD (1D)", format="%.2f", width=90),
            "Signal (1D)": st.column_config.NumberColumn("Signal (1D)", format="%.2f", width=90),
            "Chi tiết Ngày": st.column_config.TextColumn("Chi tiết Ngày", width=180),
            "RSI": st.column_config.NumberColumn("RSI", format="%.2f", width=80),
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
