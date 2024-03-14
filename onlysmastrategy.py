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
from telegram import *
import math

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
scanday = datetime.today() - timedelta(2)
active_stocks = []

def filteractivestocks(df):    
    gain = 0
    loss = 0
    tradecount = 0

    for smawindow in [11,21,30,50]:
      df["sma_" + str(smawindow)] = calculate_sma(df['close'], smawindow)

    for d in range (50, len(df)):
      prevrow = df.iloc[d-1]
      row = df.iloc[d]
     
      for smawindow in [11,21,30,50]:
          column_name = "sma_" + str(smawindow)
          smaprice = prevrow[column_name]
          if(((prevrow["open"] - smaprice) * (prevrow["close"] - smaprice)) < 0):
              if(((row["high"] - prevrow["high"])/prevrow["high"]) * 100 > 1.4):
                  tradecount = tradecount + 1
                  if(row["close"] - prevrow["high"] > 0):
                      gain = gain + 1
                  else:
                      loss = loss + 1
                  break
      
    return gain,tradecount
              
for stock, token in stock_token_mapping.items():
    start_time, end_time = maketimeframe(scanday - timedelta(400), scanday)
    df = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, scanday, "ONE_DAY",start_time, end_time, fetchlatest = False)
    if df is not None:
        gain,tradecount = filteractivestocks(df)
        
        if(tradecount > 5):
          acc = gain/tradecount
          if(acc > 0.98):
            print(stock , acc, tradecount )
        

