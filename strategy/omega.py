import os
import pandas as pd
import yfinance as yf
import numpy as np
import gurobipy as gp
from gurobipy import GRB
from datetime import datetime

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
    buy_cost = 0.001425
    sell_cost = 0.001425
    sell_tax = 0.003
    low = 0.01
    up = 1
    cost = model.addVar(lb=0, name="cost")
    w_buy = model.addVars(n, lb = 0, ub=1, name="w_buy")
    w_sell = model.addVars(n, lb = 0, ub=1, name="w_sell")
    buy_position = model.addVars(n, vtype=GRB.BINARY, name="buy_position")
    
    w = model.addVars(n, lb=0, ub=1, name="w")
    eta = model.addVars(T, lb=0, name="eta")
    psi = model.addVar(lb=-GRB.INFINITY, name="psi")
    model.setObjective(psi, GRB.MAXIMIZE)
    model.addConstr(delta * (gp.quicksum(w[j] * r_j[j] for j in range(n)) - tau) - (1 - delta) * (1 / T) * gp.quicksum(eta[t] for t in range(T)) >= psi, "Constraint_2")
    model.addConstr(buy_cost*(gp.quicksum(w_buy[j] for j in range(n)))+(sell_cost+sell_tax)*(gp.quicksum(w_sell[j] for j in range(n))) == cost, "Constraint_cost")

    for t in range(T):
        model.addConstr(eta[t] >= tau - gp.quicksum(returns.iloc[t, j] * w[j] for j in range(n)), f"Constraint_3_{t}")
    model.addConstr(gp.quicksum(w[j] for j in range(n)) == 1, "Constraint_5")
    model.addConstr(gp.quicksum(r_j[j] * w[j] for j in range(n)) >= required_return, "Constraint_6")
    for i in range(n):
        model.addConstr(w[i] == w_buy[i]-w_sell[i], f"Constraint_7_{i}")
        model.addConstr(w[i] >= buy_position[i]*low, f"Constraint_8_{i}")
        model.addConstr(w[i] <= buy_position[i]*up, f"Constraint_9_{i}")
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

def write_back(weights, stocks, market_value, data, date):
    """將投資組合更新傳回 app.py"""
    date_str = datetime.now().strftime("%Y-%m-%d")

    # 計算持股數
    total_shares = market_value * weights  # 總市值乘以權重
    # 取得每隻股票的最新股價（最後一筆股價）
    latest_prices = data.iloc[-1]  # 取得最後一筆股價

    # 計算每隻股票的持股數，將 total_shares 除以股價，並去掉值為 0 的項目
    shares_data = {stock: float(total_shares[i] / latest_prices[stock]) for i, stock in enumerate(stocks) if total_shares[i] / latest_prices[stock] != 0}

    print(f"資料處理完畢")
    
    # return market_value, shares_data ,date_str
    return market_value, shares_data ,date


def main(tau, require_return, stocks, date, last_holds,delta = 0.5):
    # 設定日期範圍
    start_date = "2024-04-01"
    end_date = "2024-06-30"
    
    yfinance_symbols = []
    for i in stocks:
        yfinance_symbols.append(i['stock_code'])
    print("正在下載股票資料...")
    data = download_data(yfinance_symbols, start_date, end_date)
    #data = yf.download(symbols, period=f"3mo", interval="1d", group_by="ticker")
    
    print("正在進行投資組合重新平衡...")
    weights, stocks = rebalance_portfolio(data, delta, tau, require_return)
    
    market_value = 0
    if last_holds:
        for i in last_holds:
            latest_price = data[i["stock_code"]].iloc[-1]  # 取得最後一筆股價（即最新股價）
            market_value += i["hold_num"] * latest_price
    if market_value == 0:
        market_value = 10000

    print("儲存結果...")
    return write_back(weights, stocks, market_value, data, end_date)
    

if __name__ == "__main__":
    main()
