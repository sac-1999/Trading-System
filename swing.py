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

listofstocks = pd.read_csv("./Info/ind_nifty500list.csv")["Symbol"].to_list()
list_of200 = pd.read_csv("./Info/ind_nifty200list.csv")["Symbol"].to_list()
f = open("./Info/stock_token_json.json", "r")
alltoken = json.load(f)
stock_token_mapping = dict([(stock, findToken(stock, "-EQ", alltoken)) for stock in listofstocks if stock not in list_of200])
token_stock_mapping = dict([(token,stock) for stock, token in stock_token_mapping.items()])
scanday = datetime.today()

for stock, token in stock_token_mapping.items():
   print(stock, token)
   start_time, end_time = maketimeframe(scanday - timedelta(400), scanday)
   df = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, scanday, "ONE_DAY", start_time, end_time, False)
   if(df is not None):
      print("done")
    