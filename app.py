from flask import Flask, render_template, request, session, redirect
from functools import wraps
import dbUtils as db
import strategy.omega as omega
from datetime import datetime


# creates a Flask application, specify a static folder on /
app = Flask(__name__, static_folder='static',static_url_path='/')
#set a secret key to hash cookies
app.config['SECRET_KEY'] = '123TyU%^&'

@app.route("/", methods=['POST','GET'])
def Home():
    portfolios = db.GetPortfolio()
    portfolio = None
    rebalance = None
    portfolio_id = session.get("portfolio_id")
    if request.method == "POST":
        data = request.form
        session["portfolio_id"] = data['portfolios']
        portfolio = db.GetPortfolioByID(session["portfolio_id"])
        rebalance = db.GetAllRebalance(session["portfolio_id"])
    if portfolio_id:
        portfolio = db.GetPortfolioByID(portfolio_id)
        rebalance = db.GetAllRebalance(portfolio_id)
    return render_template('index.html', portfolios=portfolios, portfolio=portfolio, rebalance = rebalance)

@app.route("/add_portfolio", methods=['POST','GET'])
def AddPortfolio():
    data = request.form
    init_invest = data['init_invest']
    tau = data['tau']
    require_return = data['require_return']
    strategy = data['strategy']
    if strategy == 'omega':
        strategy_id = 1
    date = datetime.now().strftime("%Y-%m-%d")
    db.AddPortfolio(init_invest, date, strategy_id)
    portfolio = db.GetLastPortfolioID()
    portfolio_id = portfolio["portfolio_id"]
    
    # 加入參數
    if portfolio_id:
        db.AddParameter(portfolio_id, "tau", tau)
        db.AddParameter(portfolio_id, "require_return", require_return)
    
    return redirect('/')

@app.route("/rebalancing", methods=['POST','GET'])
def Rebalancing():
    #第一次 rebalacing
    form = request.form
    portfolio_id = form['portfolio']
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
    return redirect("/")