#!/usr/local/bin/python
# Connect to MariaDB Platform
import mysql.connector #mariadb

try:
	#連線DB
	conn = mysql.connector.connect(
		user="root",
		password="",
		host="localhost",
		port=3306,
		database="portfolio"
	)
	#建立執行SQL指令用之cursor, 設定傳回dictionary型態的查詢結果 [{'欄位名':值, ...}, ...]
	cursor=conn.cursor(dictionary=True, buffered=True)
except mysql.connector.Error as e: # mariadb.Error as e:
	print(e)
	print("Error connecting to DB")
	exit(1)


def AddPortfolio(init_invest, date, strategy):
	sql="insert into portfolio (init_investment, create_date, strategy_id) VALUES (%s,%s,%s)"
	param=(init_invest, date, strategy,)
	cursor.execute(sql,param)
	conn.commit()
	return

def GetPortfolio():
    sql = '''
    SELECT p.*, s.strategy_name
	FROM portfolio p
	JOIN strategies s ON p.strategy_id = s.strategy_id
	WHERE 1;
    '''
    cursor.execute(sql)
    portfolio = cursor.fetchall()
    return portfolio

def GetPortfolioByID(id):
    sql = '''
    SELECT p.*, s.strategy_name
	FROM portfolio p
	JOIN strategies s ON p.strategy_id = s.strategy_id
	WHERE portfolio_id = %s;
    '''
    param=(id,)
    cursor.execute(sql,param)
    portfolio = cursor.fetchone()
    return portfolio

# add strategy parameter
def AddParameter(portfolio_id, parameter_name ,parameter_value):
    sql="insert into strategy_parameters (portfolio_id, parameter_name, parameter_value) VALUES (%s,%s,%s)"
    param=(portfolio_id, parameter_name ,parameter_value, )
    cursor.execute(sql,param)
    conn.commit()
    return

def GetLastID():
    sql = "SELECT LAST_INSERT_ID() as id FROM portfolio WHERE 1"
    cursor.execute(sql)
    portfolio_id = cursor.fetchone()
    return portfolio_id

