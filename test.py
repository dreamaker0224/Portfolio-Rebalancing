import dbUtils as db
import strategy.omega as omega


start_date = "2024-07-01"
end_date = "2024-09-30"
stocks = db.GetStockInfo("台灣 50")
yfinance_symbols = ['2330.TW']
# for i in stocks:
#     yfinance_symbols.append(i['stock_code'])
print("正在下載股票資料...")
data = omega.download_data(yfinance_symbols, start_date, end_date)
print(data)