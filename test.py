import dbUtils as db
import strategy.omega as omega


portfolio_id = 23
portfolio = db.GetPortfolioByID(portfolio_id)
parameters = db.GetParamByID(portfolio_id)
rebalance = db.GetLastRebalanceID(portfolio_id)
for i in parameters:
    if i["parameter_name"] == "tau":
        tau = float(i['parameter_value'])
    elif i["parameter_name"] == "require_return":
        require_return = float(i['parameter_value'])
stocks = db.GetStockInfo("台灣 50")
if rebalance:
    rebalance_id = rebalance["rebalance_id"]
    holds = db.GetHolds(rebalance_id)
else:
    holds = None
market_value, holds, date = omega.main(tau, require_return, stocks, portfolio['create_date'], holds)
returns = (market_value - portfolio["init_investment"])/portfolio["init_investment"]
db.AddRebalance(date, portfolio_id, market_value, returns)
rebalance = db.GetLastRebalanceID(portfolio_id)
rebalance_id = rebalance_id = rebalance["rebalance_id"]
for stock_code, hold_num in holds.items():
    db.AddHold(rebalance_id,stock_code, hold_num)