"""
CHƯƠNG TRÌNH LỌC CỔ PHIẾU REALTIME TRỰC TIẾP TỪ TRADINGVIEW (API CHÍNH THỨC)
Tài khoản: quanvcb@gmail.com
Tiêu chí lọc:
1. ĐIỀU KIỆN MỚI:
   - Đồ thị Tuần (1W): Đường xanh (MACD) hướng lên và nằm trên đường cam (Signal), Histogram đổi màu.
   - Đồ thị Ngày (1D): Histogram đổi màu, Đường xanh (MACD) hướng lên đường cam (Signal).
2. ĐIỀU KIỆN CÒN LẠI (CŨ):
   - Đồ thị Tuần (1W): Đường xanh (MACD) cắt lên đường cam (Signal).
Thêm cột 'Điều kiện lọc' trong bảng kết quả để phân loại rõ ràng.
"""

import sys
import time
import requests
import pandas as pd
from datetime import datetime

def rating_to_text(val):
    if val is None:
        return "N/A"
    if val >= 0.5:
        return "MUA MẠNH"
    elif val > 0.1:
        return "MUA"
    elif val <= -0.5:
        return "BÁN MẠNH"
    elif val < -0.1:
        return "BÁN"
    else:
        return "TRUNG TÍNH"

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

class TradingViewScreener:
    def __init__(self, username="quanvcb@gmail.com", password="Quochien@2021"):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://vn.tradingview.com/"
        })
        self.is_logged_in = False
        self.user_info = None

    def login(self):
        """Đăng nhập vào tài khoản TradingView để lấy phiên làm việc"""
        login_url = "https://www.tradingview.com/accounts/signin/"
        payload = {
            "username": self.username,
            "password": self.password,
            "remember": "true"
        }
        try:
            res = self.session.post(login_url, data=payload, timeout=15)
            if res.status_code == 200:
                data = res.json()
                if "error" in data and not data["error"]:
                    self.is_logged_in = True
                    self.user_info = data.get("user", {})
                    username = self.user_info.get("username", self.username)
                    print(f"✅ Đăng nhập TradingView thành công! Tài khoản: {username}")
                    return True
                else:
                    print(f"⚠️ Đăng nhập không thành công: {data.get('error')}")
            else:
                print(f"⚠️ Phản hồi đăng nhập HTTP {res.status_code}")
        except Exception as e:
            print(f"❌ Lỗi kết nối đăng nhập: {e}")
        return False

    def scan_macd_weekly_hose(self, min_volume=0):
        """
        Quét toàn bộ cổ phiếu sàn HOSE và lọc theo 2 điều kiện:
        - Điều kiện 1 (cũ): Tuần MACD cắt lên Signal
        - Điều kiện 2 (mới): Tuần MACD hướng lên & nằm trên Signal, Hist đổi màu;
                             Ngày Hist đổi màu, MACD hướng lên Signal
        Phân loại rõ vào cột 'Điều kiện lọc'.
        """
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
                "change",                   # 3: % Thay đổi giá
                "volume",                   # 4: Khối lượng giao dịch
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
            res = self.session.post(scan_url, json=payload, timeout=20)
            if res.status_code != 200:
                print(f"❌ Lỗi truy vấn bộ lọc (HTTP {res.status_code}): {res.text[:100]}")
                return pd.DataFrame()

            data = res.json()
            items = data.get("data", [])

            records = []
            for item in items:
                d = item.get("d", [])
                if len(d) < 24:
                    continue

                symbol = d[0]
                name = d[1]
                close = d[2]
                change = d[3]
                volume = d[4]

                m_d, s_d, h_d = d[5], d[6], d[7]
                m_d1, s_d1, h_d1 = d[8], d[9], d[10]
                m_d2, s_d2, h_d2 = d[11], d[12], d[13]

                m_w, s_w, h_w = d[14], d[15], d[16]
                m_w1, s_w1, h_w1 = d[17], d[18], d[19]

                rsi = d[20]
                rec_str = rating_to_text(d[21])
                rec_ma = rating_to_text(d[22])
                rec_osc = rating_to_text(d[23])
                ma_osc_desc = f"MA: {rec_ma}, Dao động: {rec_osc}"

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
                #   + Histogram tuần đổi màu: h_w1 <= 0 và h_w > 0 (đổi sang xanh) HOẶC h_w > h_w1 (xanh nhạt -> xanh đậm)
                # - Khung Ngày (1D):
                #   + MACD Histogram đổi màu (color_d != color_d1)
                #   + Đường xanh hướng lên đường cam (m_d > m_d1 và h_d > h_d1)
                cond_new = False
                day_status_desc = ""
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
                                    day_status_desc = f"{c_d1} ➔ {c_d} (Dưới cam hướng lên)"
                                else:
                                    day_status_desc = f"{c_d1} ➔ {c_d} (Trên cam hướng lên)"

                # Phân loại vào cột 'Điều kiện lọc'
                if cond_old and cond_new:
                    filter_cond_label = "Thỏa mãn cả 2 điều kiện"
                elif cond_new:
                    filter_cond_label = "ĐK mới (Tuần MACD > Signal + Ngày hướng lên)"
                elif cond_old:
                    filter_cond_label = "ĐK còn lại (Tuần MACD cắt lên Signal)"
                else:
                    continue  # Không thỏa mãn điều kiện nào thì bỏ qua

                tv_link = f"https://vn.tradingview.com/chart/xKsA49eB/?symbol=HOSE:{symbol}"

                records.append({
                    "Mã CP": symbol,
                    "Điều kiện lọc": filter_cond_label,
                    "Xếp hạng kỹ thuật": rec_str,
                    "Đánh giá MA / Dao động": ma_osc_desc,
                    "RSI": round(rsi, 2) if rsi is not None else 0,
                    "Giá (VNĐ)": close,
                    "Thay đổi (%)": round(change, 2) if change is not None else 0.0,
                    "Khối lượng": int(volume) if volume is not None else 0,
                    "MACD (1W)": round(m_w, 2) if m_w is not None else 0,
                    "Signal (1W)": round(s_w, 2) if s_w is not None else 0,
                    "Histogram (1W)": round(h_w, 2) if h_w is not None else 0,
                    "MACD (1D)": round(m_d, 2) if m_d is not None else 0,
                    "Signal (1D)": round(s_d, 2) if s_d is not None else 0,
                    "Histogram (1D)": round(h_d, 2) if h_d is not None else 0,
                    "Chi tiết Ngày": day_status_desc if day_status_desc else "N/A",
                    "Tên Công Ty": name,
                    "Link TradingView": tv_link
                })

            df = pd.DataFrame(records)
            if not df.empty:
                # Sắp xếp ưu tiên:
                # 1. Nhóm điều kiện: Thỏa mãn cả 2 -> ĐK mới -> ĐK còn lại
                # 2. Xếp hạng kỹ thuật: MUA MẠNH -> MUA -> TRUNG TÍNH -> BÁN -> BÁN MẠNH
                # 3. RSI giảm dần
                cond_order = {
                    "Thỏa mãn cả 2 điều kiện": 1,
                    "ĐK mới (Tuần MACD > Signal + Ngày hướng lên)": 2,
                    "ĐK còn lại (Tuần MACD cắt lên Signal)": 3
                }
                rank_map = {
                    "MUA MẠNH": 1,
                    "MUA": 2,
                    "TRUNG TÍNH": 3,
                    "BÁN": 4,
                    "BÁN MẠNH": 5
                }
                df["_cond_rank"] = df["Điều kiện lọc"].map(lambda x: cond_order.get(x, 99))
                df["_rec_rank"] = df["Xếp hạng kỹ thuật"].map(lambda x: rank_map.get(x, 99))
                df = df.sort_values(by=["_cond_rank", "_rec_rank", "RSI"], ascending=[True, True, False]).drop(columns=["_cond_rank", "_rec_rank"]).reset_index(drop=True)

            if not df.empty and min_volume > 0:
                df = df[df["Khối lượng"] >= min_volume].reset_index(drop=True)

            return df

        except Exception as e:
            print(f"❌ Lỗi khi quét bộ lọc: {e}")
            return pd.DataFrame()

def main():
    print("=" * 95)
    print("📈 TRADINGVIEW REALTIME STOCK SCREENER - VNINDEX (HOSE)")
    print("🎯 BỘ LỌC ĐA ĐIỀU KIỆN:")
    print("   1. [ĐIỀU KIỆN MỚI]: Tuần (1W) MACD Xanh hướng lên & trên Signal Cam, Histogram đổi màu;")
    print("                        Ngày (1D) Histogram đổi màu, MACD Xanh hướng lên Signal Cam.")
    print("   2. [ĐIỀU KIỆN CÒN LẠI]: Tuần (1W) MACD Xanh cắt lên Signal Cam.")
    print("=" * 95)

    screener = TradingViewScreener()
    print("\n🔐 Đang kết nối tài khoản TradingView...")
    screener.login()

    print("\n⚡ Đang thực hiện quét toàn bộ cổ phiếu sàn HOSE qua TradingView Scanner API...")
    df_result = screener.scan_macd_weekly_hose(min_volume=0)

    if df_result.empty:
        print("⚠️ Hiện tại chưa có mã nào thỏa mãn điều kiện hoặc có lỗi khi tải.")
        return

    print(f"\n🎉 Tìm thấy {len(df_result)} cổ phiếu thỏa mãn các tiêu chí lọc:")
    print("-" * 120)
    
    show_cols = [
        "Mã CP", 
        "Điều kiện lọc",
        "Xếp hạng kỹ thuật", 
        "Giá (VNĐ)", 
        "Thay đổi (%)", 
        "Khối lượng",
        "MACD (1W)",
        "Signal (1W)",
        "MACD (1D)",
        "Signal (1D)"
    ]
    print(df_result[show_cols].to_string(index=False))
    print("-" * 120)

    # Thống kê số lượng
    c_both = len(df_result[df_result["Điều kiện lọc"].str.contains("cả 2")])
    c_new = len(df_result[df_result["Điều kiện lọc"].str.contains("ĐK mới")])
    c_old = len(df_result[df_result["Điều kiện lọc"].str.contains("ĐK còn lại")])
    print(f"\n📊 Phân bổ: {c_both} mã đạt cả 2 ĐK | {c_new} mã ĐK mới | {c_old} mã ĐK còn lại.")

    output_csv = "ket_qua_loc_tradingview.csv"
    df_result.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"💾 Đã lưu kết quả chi tiết ra file: {output_csv}")

if __name__ == "__main__":
    main()
