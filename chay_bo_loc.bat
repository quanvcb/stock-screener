@echo off
chcp 65001 >nul
echo ======================================================================
echo   HE THONG LOC CO PHIEU TRADINGVIEW REALTIME (HOSE - TUAN & NGAY)
echo   Tieu chi:
echo   - DK Moi: Tuan MACD Xanh > Cam huong len, Hist doi mau.
echo             Ngay Hist doi mau, MACD Xanh huong len Cam.
echo   - DK Con lai: Tuan MACD Xanh cat len Signal Cam.
echo ======================================================================
echo.
echo [1] Chay Web Dashboard truc tuyen (Giao dien Web Streamlit)
echo [2] Quet nhanh tren man hinh Console (Luu ket qua ra CSV)
echo.
set /p opt="Vui long chon [1 hoac 2]: "

if "%opt%"=="1" (
    echo.
    echo Dang khoi dong Web Dashboard tren trinh duyet...
    streamlit run tv_dashboard_web.py
) else (
    echo.
    echo Dang quet du lieu tu TradingView...
    python tv_screener_realtime.py
    pause
)
