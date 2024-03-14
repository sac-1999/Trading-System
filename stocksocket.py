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
symboldf = pd.read_csv("./Info/ind_nifty200list.csv")
stocklist = symboldf["Symbol"].to_list()

tokenlist = {}
with open("./Info/stock_token_json.json", "r") as infile:
    tokenlist = json.load(infile)


stocktoken_dict = dict([(stock, findToken(stock, "-EQ", tokenlist)) for stock in stocklist])
scanday = datetime.today()
swingbullishlist = filterstock(fetchobj, angleobj, stocktoken_dict, scanday)


low_high_list = dict([(stock,fetchLastdays(stock,scanday - timedelta(1), 1)) for stock, token in swingbullishlist.items()])
tokentosubscribe = list(swingbullishlist.values())
tokentostockmapping  = {v: k for k, v in stocktoken_dict.items()}
print(tokentosubscribe)

lock = threading.Lock()
correlation_id = "abc123"
mode = 1
token_list = [
    {
        "exchangeType": 1,
        "tokens": tokentosubscribe
    }
]

stockabove_pct = []

sws = SmartWebSocketV2(authtoken, apikey, clientid, feedtoken)

def on_data(wsapp, message):
    logger.info("Ticks: {}".format(message))
    token = message.get("token")
    # if(token is not None):
    #     stock = tokentostockmapping.get(token)
    #     if(stock is not None):
    #         if(stock not in stockabove_pct):   
    #             currprice = message.get("last_traded_price")/100
    #             lasthigh = low_high_list[stock][1]
    #             lastdayclose = low_high_list[stock][2]
    #             low = low_high_list[stock][0]
    #             pct_change = ((currprice - lastdayclose)/lastdayclose) * 100
    #             # print(stock, currprice, lasthigh, lastdayclose, low, round(pct_change, 2))
    #             if(pct_change > 1.4 and stock not in stockabove_pct):
    #                 stockabove_pct.append(stock) 
    #                 print(stockabove_pct)



def on_open(wsapp):
    logger.info("on open")
    sws.subscribe(correlation_id, mode, token_list)

def on_error(wsapp, error):
    logger.error(error)

def on_close(wsapp):
    logger.info("Close")



def close_connection():
    sws.close_connection()


# Assign the callbacks.
sws.on_open = on_open
sws.on_data = on_data
sws.on_error = on_error
sws.on_close = on_close


threading.Thread(target=sws.connect(), args=()).start()

def scan(df, low, high, close, stock, scanday, token):
    with open("daystatus.json", "r") as fin:
        allrecords = json.load(fin)

    key = stock + "{}{}{}".format(scanday.day, scanday.month, scanday.year)
    if allrecords.get(key) is not None:
        return True

    df = calcVWAP(df)

    slprice, entryprice, tsindex, vwapprice = checkforbullish(df, high, 25)
    if(slprice > 0 and entryprice >= high):
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


def synclivestocks(fetchobj, angleobj,scanday, timeframe):
    start_time, end_time = maketimeframe(scanday, scanday)
    
    while(True):
        final_stock_dict = dict([(stock, findToken(stock, "-EQ", tokenlist)) for stock in stockabove_pct])
        for stock, token in final_stock_dict.items():
            df = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, scanday, timeframe,start_time, end_time, fetchlatest = True)
            if(df is None or len(df) == 0):
                print(stock, " unsuccessful sync ", scanday)
                continue
            else:
                print(stock, ": successfully fetched data for sync ", scanday)
    


def scanstocks(scanday, timeframe):
    while(True):
        final_stock_dict = dict([(stock, findToken(stock, "-EQ", tokenlist)) for stock in stockabove_pct])
        folder = "./data/"+timeframe+"/"
        for stock, token in final_stock_dict.items():
            try:
              low, high, close = fetchLastdays(stock,scanday - timedelta(1), 1)
              filename = folder + "{}/{}-{}-{}.csv".format(stock, scanday.day, scanday.month, scanday.year)
              if(os.path.exists(filename)):
                  df = pd.read_csv(filename)
                  scan(df, low, high,close, stock, scanday, token)

            except Exception as e:
              print("An error occurred: in stock scanning", stock, "   " ,e)



t1 = threading.Thread(target=synclivestocks, args=(fetchobj, angleobj, scanday, "ONE_MINUTE"))
t2 = threading.Thread(target=scanstocks, args=(scanday,"ONE_MINUTE"))
t2.start()
t1.start()

t1.join()
t2.join()