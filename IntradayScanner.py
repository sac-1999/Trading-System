import json
import json
import datetime
from datetime import timedelta
import pandas as pd
import os
import sys
from anglecreds import angleone
import json
from fetchdata import fetchdata
from savestockdata import downloadandsaveForBacktesting
from strategy import checkforbearish, checkforbullish
import threading
from savetrade import backtest_save
from levels import findlevels, fetchLevels
import time
from utils import *


angleobj = angleone()
fetchobj = fetchdata(3,1000)

stock_token = {}
with open("./Info/stock_token_json.json", "r") as infile:
    stock_token = json.load(infile)

session = angleobj.connect()
if(session.get("status") == True):
    authtoken = session['data']['jwtToken']
    refreshtoken = session['data']['refreshToken']
    feedtoken = angleobj.smartapi.getfeedToken()
    res = angleobj.smartapi.getProfile(refreshtoken)
    connection_status = angleobj.smartapi.generateToken(refreshtoken)
    print("connection is valid")
else:
  print("session invalid : ", session.message)
  exit()


# df, low, high, stock, scanday, token
def scan(df, low, high, close, stock, scanday, token):
    with open("daystatus.json", "r") as fin:
        allrecords = json.load(fin)

    key = stock + "{}{}{}".format(scanday.day, scanday.month, scanday.year)
    if allrecords.get(key) is not None:
        return True

    df = calcVWAP(df)

    slprice, entryprice, tsindex, vwapprice = checkforbullish(df, high, 25)
    if(slprice > 0 and entryprice >= high):
          print("")
          if(((entryprice - close)/close)*100 < 1.5):
              return False
          ts = df.loc[tsindex,"timestamp"]
          parsed_datetime = datetime.fromisoformat(ts[:-6])  # Remove the timezone part for parsing
          hour = parsed_datetime.hour
          minute = parsed_datetime.minute

          if not (hour < 12 or (hour == 12 and minute < 30)):
              return

          vwapMsl = (vwapprice - slprice)/slprice
          if(vwapMsl < 0.005 or True):
              type = "buy"
              levels = fetchLevels(stock,scanday - timedelta(1) , "bullish", entryprice)
              print(stock, "    ", levels)
              allrecords[key] = {"day" : scanday.isoformat(),
                                  "entryprice" : entryprice,
                                   "slprice" :  slprice,
                                    "levels" :  levels,
                                    "type" : type,
                                    "stock" : stock,
                                    "token" : token,
                                    "timestamp" : ts,
                                    "isnew" : True}


              with open("daystatus.json", "w") as fout:
                  json.dump(allrecords, fout)

              print(stock, "selected for bullish ", ts)
              return True
          
    slprice, entryprice, tsindex, vwapprice = checkforbearish(df,low, 25)

    if(slprice > 0 and entryprice <= low):
          vwapMsl = (vwapprice - slprice)/slprice

          if(((close - entryprice)/close)*100 < 1.5):
              return False
          
          ts = df.loc[tsindex,"timestamp"]
          parsed_datetime = datetime.fromisoformat(ts[:-6])  # Remove the timezone part for parsing
          hour = parsed_datetime.hour
          minute = parsed_datetime.minute

          if not (hour < 12 or (hour == 12 and minute < 30)):
              return

          if(vwapMsl > -0.0025 or True):
              type = "sell"
              levels = fetchLevels(stock,scanday - timedelta(1), "bearish", entryprice)
              allrecords[key] = {"day" : scanday.isoformat(),
                                  "entryprice" : entryprice,
                                   "slprice" :  slprice,
                                    "levels" :  levels,
                                    "type" : type,
                                    "stock" : stock,
                                    "token" : token,
                                    "timestamp" : ts,
                                    "isnew" : True}

              with open("daystatus.json", "w") as fout:
                  json.dump(allrecords, fout)

              print(stock, "selected for bearish ", ts)
              return True

symboldf = pd.read_csv("./Info/ind_nifty200list.csv")
stocklist = symboldf["Symbol"].to_list()

def scanstocks(listofstock, scanday, timeframe,iteration, backtest):
    while(iteration >0 ):
        if(backtest == True):
            iteration = iteration - 1

        folder = "./data/"+timeframe+"/"
        for stock, token in listofstock.items():
            try:
              low, high, close = fetchLastdays(stock,scanday - timedelta(1), 1)
              filename = folder + "{}/{}-{}-{}.csv".format(stock, scanday.day, scanday.month, scanday.year)
              if(os.path.exists(filename)):
                  df = pd.read_csv(filename)
                  scan(df, low, high,close, stock, scanday, token)
                #   print(stock," : scan done for - ", scanday.day)

            except Exception as e:
              print("An error occurred: in stock scanning", stock, "   " ,e)


import json
with open("daystatus.json", "w") as fout:
  json.dump({}, fout)


# for i in range(2,20):
endday = datetime.today() - timedelta(0)
uptoday = endday - timedelta(1)

listofstock = symboldf["Symbol"].to_list()
tokendata = json.load(open("./Info/stock_token_json.json", "r"))
stocktoken_dict = dict([(stock, findToken(stock, "-EQ", tokendata)) for stock in listofstock])

timeframe = "ONE_MINUTE"

syncDailydata(fetchobj, angleobj, stocktoken_dict, uptoday)

filtered_stocks = {}
for stock, token in stocktoken_dict.items():
    start_time, end_time = maketimeframe(uptoday - timedelta(400), uptoday)
    df = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, uptoday, "ONE_DAY", start_time, end_time, False)
    if(df is not None):
        if(checkPossibleStockForDay(stock, df, endday)):
            filtered_stocks[stock] = token


#synclivemarket(fetchobj, angleobj,listofstocks, scanday, timeframe, iteration, backtest):
            
#scanstocks(listofstock, scanday, timeframe,iteration, backtest):
        
t1 = threading.Thread(target=synclivemarket, args=(fetchobj, angleobj,filtered_stocks, endday, "ONE_MINUTE", 1, False))
t1.start()
t2 = threading.Thread(target=scanstocks, args=(filtered_stocks, endday,"ONE_MINUTE",2, False))
t2.start()


# buildstockimage(fetchobj, angleobj, listofstock, endday)

saving_time_start = time.time()
while(datetime.fromtimestamp(saving_time_start).hour < 15 or True):
    if(time.time() - saving_time_start > 50):
        buildstockimage(fetchobj, angleobj, listofstock, endday)
        saving_time_start = time.time()


# t1.join()
# t2.join()