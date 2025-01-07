import dbUtils as db
import strategy.omega as omega


portfolio_id = 17
portfolio = db.GetPortfolioByID(portfolio_id)
parameters = db.GetParamByID(portfolio_id)
for i in parameters:
    if i["parameter_name"] == "tau":
        tau = float(i['parameter_value'])
    elif i["parameter_name"] == "require_return":
        require_return = float(i['parameter_value'])
stocks = db.GetStockInfo("台灣 50")
holds = None
market_value, holds, date = omega.main(tau, require_return, stocks, portfolio['create_date'], holds)
print(holds)