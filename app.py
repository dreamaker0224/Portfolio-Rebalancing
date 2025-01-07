from flask import Flask, render_template, request, session, redirect
from functools import wraps
import dbUtils as db
import strategy.omega as omega
from datetime import datetime


# creates a Flask application, specify a static folder on /
app = Flask(__name__, static_folder='static',static_url_path='/')
#set a secret key to hash cookies
app.config['SECRET_KEY'] = '123TyU%^&'

#define a function wrapper to check login session
def login_required(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		loginID = session.get('loginID')
		if not loginID:
			return redirect('/loginPage.html')
		return f(*args, **kwargs)
	return wrapper


@app.route("/")
def Home():
    portfolio = db.GetPortfolio(3)
    return render_template('index.html', portfolio = portfolio)

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
    return redirect('/')