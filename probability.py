from logzero import logger
from anglecreds import angleone
import json
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from logzero import logger
import pandas as pd
from utils import *
from fetchdata import fetchdata
from strategy import checkforbearish, checkforbullish
import threading
from savetrade import backtest_save
from levels import findlevels, fetchLevels

angleobj = angleone()
fetchobj = fetchdata(3,1000)

session = angleobj.connect()
if(session.get("status") == True):
    authtoken = session['data']['jwtToken']
    apikey = angleobj.apikey
    clientid = angleobj.clientid
    refreshtoken = session['data']['refreshToken']
    feedtoken = angleobj.smartapi.getfeedToken()
    res = angleobj.smartapi.getProfile(refreshtoken)
    connection_status = angleobj.smartapi.generateToken(refreshtoken)
    print("connection is valid")
else:
  print("session invalid : ", session.message)
  exit()


listofstocks = pd.read_csv("./Info/ind_nifty200list.csv")["Symbol"].to_list()
f = open("./Info/stock_token_json.json", "r")
alltoken = json.load(f)
stock_token_mapping = dict([(stock, findToken(stock, "-EQ", alltoken)) for stock in listofstocks])
token_stock_mapping = dict([(token,stock) for stock, token in stock_token_mapping.items()])

scanday = datetime.today()
stock_low_high_list = dict([(stock,fetchLastdays(stock, scanday - timedelta(1))) for stock in listofstocks])



def createReport(stock, df, smawindow):
    copydf = df.copy()
    copydf["sma"] = calculate_sma(copydf['close'], smawindow)
  
    above_sma_bull = 0
    below_sma_bull = 0
    total_positive = 0

    for index, row in copydf.iterrows():
      
      if(index > 10):
        pct = ((row["close"] - row["open"])/ row["open"]) * 100
        if(pct > 0):
          total_positive += 1 
          if(row["open"] < row["sma"] and row["high"] >= prevrow["high"]):
            below_sma_bull += 1

          elif(row["open"] > row["sma"] and row["high"] >= prevrow["high"]):
            above_sma_bull += 1

      prevrow = row


def createMystrategyReport(stock, df, smawindow):
    copydf = df.copy()
    copydf["sma"] = calculate_sma(copydf['close'], smawindow)

    total_taken_trades = 1
    closeinprofit = 0
    closeinloss = 0

    for index, row in copydf.iterrows():
      if(row["open"] > row["sma"]):
        if(index > 10):
          entryprice = prevrow["close"] + prevrow["close"] * 0.014
          if(row["high"] >= prevrow["high"] and row["high"] >= entryprice):
            total_taken_trades += 1 
            p_l = row["close"] - entryprice
            if(p_l > 0):
              closeinprofit += 1
            
      prevrow = row

    print(stock, total_taken_trades)
    return (closeinprofit/total_taken_trades, -1)

today = datetime.today()

for stock, token in stock_token_mapping.items():
  start_time, end_time = maketimeframe(today - timedelta(500), today)
  df = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, today, "ONE_DAY", start_time, end_time, False)

  if(df is not None):
    x_axis = []
    y_abovebull = []
    y_belowbull = []
    for sma in range(11, 21):
        abovesmabullratio, belowsmabullratio = createMystrategyReport(stock, df, sma)
        if(abovesmabullratio != 0):
          x_axis.append(sma)
          y_abovebull.append(abovesmabullratio)
        # y_belowbull.append(belowsmabullratio)
    
    average = sum(y_abovebull) / len(y_abovebull)
    if(len(y_abovebull)>0 and average<0.45):
      plt.scatter(x_axis, y_abovebull, color = "green")
      # plt.scatter(x_axis, y_belowbull, color = "red")
      plt.title(stock)
      plt.savefig("dates/sma/" + stock + ".jpg")
      plt.close()


  
         
         
        
# equity_bull_stocks, equity_bear_stocks = filterstock(fetchobj, angleobj, stock_token_mapping, scanday, 50)



