import os
import pandas as pd
import yfinance as yf
import numpy as np
import gurobipy as gp
from gurobipy import GRB
from datetime import datetime

# 股票代碼
stock_data = [
    "2330", "2317", "2454", "2308", "2382", "2881", "2891", "2882", "3711",
    "2303", "2412", "2357", "2886", "2884", "2885", "1216", "2345", "2892",
    "3231", "3034", "6669", "2883", "2890", "2327", "2379", "3008", "5880",
    "2880", "3661", "2603", "2002", "1101", "2887", "4938", "2207", "2301",
    "3017", "3037", "6446", "3045", "1303", "2395", "4904", "5876", "2912",
    "1301", "2609", "5871", "1326", "6505"
]

# 將代碼轉換為 yfinance 格式
yfinance_symbols = [f"{code}.TW" for code in stock_data]

# 設定參數
delta = 0.5  # 風險偏好參數
tau = 0.0  # 最低收益閾值
required_return = 0  # 最低收益限制
input_excel = "portfolio.xlsx"

def download_data(symbols, start_date, end_date):
    """下載特定日期範圍的股票資料"""
    data = yf.download(symbols, start=start_date, end=end_date, interval="1d", group_by="ticker")
    close_prices = {symbol: data[symbol]["Close"] for symbol in symbols if symbol in data}
    df = pd.DataFrame(close_prices)
    if df.empty:
        raise ValueError("下載的股票資料為空，請檢查股票代碼或網路連線。")
    return df

def optimize_portfolio(returns, delta, tau, required_return):
    """使用 Gurobi 根據模型進行投資組合優化"""
    T, n = returns.shape
    if T == 0 or n == 0:
        raise ValueError("返回資料為空，無法進行優化。請檢查下載的資料。")

    avg_returns = returns.mean(axis=0)
    r_j = avg_returns.values

    model = gp.Model("OmegaPortfolio")
    w = model.addVars(n, lb=0, ub=1, name="w")
    eta = model.addVars(T, lb=0, name="eta")
    psi = model.addVar(lb=-GRB.INFINITY, name="psi")
    model.setObjective(psi, GRB.MAXIMIZE)
    model.addConstr(delta * (gp.quicksum(w[j] * r_j[j] for j in range(n)) - tau) - (1 - delta) * (1 / T) * gp.quicksum(eta[t] for t in range(T)) >= psi, "Constraint_2")

    for t in range(T):
        model.addConstr(eta[t] >= tau - gp.quicksum(returns.iloc[t, j] * w[j] for j in range(n)), f"Constraint_3_{t}")
    model.addConstr(gp.quicksum(w[j] for j in range(n)) == 1, "Constraint_5")
    model.addConstr(gp.quicksum(r_j[j] * w[j] for j in range(n)) >= required_return, "Constraint_6")
    model.optimize()

    if model.status == GRB.OPTIMAL:
        weights = np.array([w[j].X for j in range(n)])
        return weights
    else:
        raise ValueError("No optimal solution found.")

def rebalance_portfolio(data, delta, tau, required_return):
    """根據模型進行重新平衡"""
    returns = data.pct_change().dropna()
    weights = optimize_portfolio(returns, delta, tau, required_return)
    selected_stocks = data.columns
    return weights, selected_stocks

def write_portfolio_to_excel(weights, stocks, market_value, data, output_path):
    """將投資組合更新寫入 Excel，包括 portfolio 和 hold 工作表"""
    date_str = datetime.now().strftime("%Y-%m-%d")

    # 計算持股數
    total_shares = market_value * weights  # 總市值乘以權重
    # 取得每隻股票的最新股價（最後一筆股價）
    latest_prices = data.iloc[-1]  # 取得最後一筆股價

    # 計算每隻股票的持股數，將 total_shares 除以股價
    shares_data = {stock: total_shares[i] / latest_prices[stock] for i, stock in enumerate(stocks)}


    if os.path.exists(output_path):
        with pd.ExcelWriter(output_path, mode="a", if_sheet_exists="overlay") as writer:
            # 更新 portfolio 工作表
            portfolio_df = pd.DataFrame({
                "Date": [date_str],
                "Market Value": [market_value],
                **dict(zip(stocks, weights))
            })
            portfolio_df.to_excel(writer, sheet_name="portfolio", index=False, startrow=writer.sheets["portfolio"].max_row, header=False)

            # 更新 hold 工作表
            hold_df = pd.DataFrame({
                "Date": [date_str],
                "Market Value": [market_value],
                **shares_data
            })
            hold_df.to_excel(writer, sheet_name="hold", index=False, startrow=writer.sheets["hold"].max_row, header=False)
    else:
        raise ValueError("portfolio.xlsx 儲存錯誤")

    print(f"資料已儲存到 {output_path}")


def initialize_excel(output_path):
    """初始化 portfolio 和 hold 工作表"""
    initial_date = datetime.now().strftime("%Y-%m-%d")
    initial_market_value = 10000  # 初始投資金額

    # 初始化 portfolio 工作表
    portfolio_data = {
        "Date": [initial_date],
        "Market Value": [initial_market_value]
    }

    # 初始化 hold 工作表
    hold_data = {
        "Date": [initial_date],
        "Market Value": [initial_market_value]
    }

    for stock in stock_data:
        portfolio_data[stock] = [0]  # 初始化權重為 0
        hold_data[stock] = [0]       # 初始化持股數為 0

    with pd.ExcelWriter(output_path) as writer:
        pd.DataFrame(portfolio_data).to_excel(writer, sheet_name="portfolio", index=False)
        pd.DataFrame(hold_data).to_excel(writer, sheet_name="hold", index=False)

    print(f"已初始化 {output_path} 檔案，請重新執行程式。")

def main():
    if not os.path.exists(input_excel):
        print(f"{input_excel} 不存在，正在初始化資料...")
        initialize_excel(input_excel)
        return

    # 讀取 Excel 資料
    try:
        portfolio_df = pd.read_excel(input_excel, sheet_name="portfolio")
        hold_df = pd.read_excel(input_excel, sheet_name="hold")
    except ValueError as e:
        print(f"讀取 Excel 時發生錯誤: {e}")
        print("正在重新初始化資料...")
        initialize_excel(input_excel)
        return

    # 檢查資料是否有效
    if portfolio_df.empty or hold_df.empty:
        print("portfolio 或 hold 工作表為空，正在初始化資料...")
        initialize_excel(input_excel)
        return

    # 確定最新日期和市值
    last_date = portfolio_df["Date"].max()
    if pd.isna(last_date):
        raise ValueError("portfolio.xlsx 的 portfolio 工作表中沒有有效的日期資料。")

    # 確認是否有符合條件的行
    latest_row = portfolio_df[portfolio_df["Date"] == last_date]
    if latest_row.empty:
        raise ValueError(f"無法找到日期為 {last_date} 的市值資料，請檢查資料是否完整。")


    # 設定日期範圍
    start_date = "2024-06-01"
    end_date = "2024-08-31"

    print("正在下載股票資料...")
    data = download_data(yfinance_symbols, start_date, end_date)
    #data = yf.download(symbols, period=f"3mo", interval="1d", group_by="ticker")
    
    print("正在進行投資組合重新平衡...")
    weights, stocks = rebalance_portfolio(data, delta, tau, required_return)
    
    
    # 取得最後一行的持有股數
    last_row_holdings = hold_df.iloc[-1, 2:].values  

    # 取得最後一行對應的股票代號
    stock_codes = hold_df.columns[2:52].values  

    market_value = 0
    for stock, holding in zip(data, last_row_holdings):
        if stock in data.columns:
            latest_price = data[stock].iloc[-1]  # 取得最後一筆股價（即最新股價）
            market_value += holding * latest_price
    if market_value == 0:
        market_value = 10000


    print("儲存結果...")
    write_portfolio_to_excel(weights, stocks, market_value, data, input_excel)

if __name__ == "__main__":
    main()
