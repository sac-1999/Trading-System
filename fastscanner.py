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

with open("daystatus.json", "r") as fin:
    overall_maintainer = json.load(fin)

# print(overall_maintainer)
scanday = datetime.today()
syncDailydata(fetchobj, angleobj, stock_token_mapping, scanday-timedelta(1))
maintainerdaykey = "{}{}{}".format(scanday.day, scanday.month, scanday.year)

day_maintainer = overall_maintainer.get(maintainerdaykey)

if(day_maintainer is None):
    day_maintainer = {}

for stock, token in stock_token_mapping.items():
    if(day_maintainer.get(stock) is not None):
        day_maintainer[stock]["is_above_sma"] = filterstock(fetchobj, angleobj, stock, token, scanday - timedelta(1), 11)
        continue
    _, _, _, high, low, close, _ = fetchLastdays(stock, scanday - timedelta(1))
    day_maintainer[stock]= {
                        "is_above_sma": filterstock(fetchobj, angleobj, stock, token, scanday - timedelta(1), 11),
                        "watching": False,
                        "is_entry_made" : False,
                        "stop_loss": -1,
                        "entry_price": -1,
                        "target":-1,
                        "telegram_notify":True,
                        "lastdaylow":low,
                        "lastdayhigh":high,
                        "lastdayclose": close,
                        "token":token,
                        "entry_timestamp":""} 
    
overall_maintainer[maintainerdaykey] = day_maintainer
with open("daystatus.json", "w") as fout:
    json.dump(overall_maintainer,fout)


# with open("daystatus.json", "w") as fout:
#   json.dump({}, fout)

correlation_id = "abc123"
mode = 2
token_list = [
    {
        "exchangeType": 1,
        "tokens": list(stock_token_mapping.values())
    }
]

lock = threading.Lock()


possible_buys = []
possible_sells = []

sws = SmartWebSocketV2(authtoken, apikey, clientid, feedtoken)


def on_data(wsapp, message):
    
    token = message.get("token")
    day_high_price = message.get("high_price_of_the_day")/100
    closed_price = message["closed_price"]/100    
    day_low_price = message.get("low_price_of_the_day")/100
    
    if(token is not None):
        stock = token_stock_mapping[token]
        stockstatus = day_maintainer[stock]
        
        selection_pct = 0.015
        if(stock in ["TCS", "INFY", "RELIANCE","HDFCBANK", "ICICIBANK", "SBIN"]):
            selection_pct = 0.08

        if(stockstatus["watching"] == True):
            return

        if(stockstatus["is_above_sma"]):
            if((day_high_price - closed_price)/closed_price > selection_pct):
                with lock:
                    day_maintainer[stock]["watching"] = True

        if(not stockstatus["is_above_sma"]):
            if((day_low_price - closed_price)/closed_price < -1 * selection_pct):
                with lock:
                    day_maintainer[stock]["watching"] = True

        return
                        
            
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


def synclivestocks(fetchobj, angleobj,scanday, timeframe):
    start_time, end_time = maketimeframe(scanday, scanday)
    while(True):
        try:
            with lock:
                day_maintainer_copy = day_maintainer.copy()
                
            watchstocks = [(stock,details["token"]) for stock,details in day_maintainer_copy.items() if (details["watching"] == True and details["telegram_notify"] == True)]
            
            if(len(watchstocks)<=0):
                print("empty list")
                time.sleep(10)
                
            for stock, token in watchstocks:
                df = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, scanday, timeframe,start_time, end_time, fetchlatest = True)
                if(df is None or len(df) == 0):
                    print(stock, " unsuccessful sync ", scanday)
                    continue
                else:
                    print(stock, ": successfully fetched data for sync ", scanday)
        
        except Exception as e:
                print("Error in synclivestocks", stock, "   " ,e)
            


def processstock(stock, stock_status):
    foldertype = "buy" if stock_status["is_above_sma"] else "sell"
    tradetype = "bullish" if stock_status["is_above_sma"] else "bearish"
    color = "red" if stock_status["is_above_sma"] else "green"

    ts = stock_status["entry_timestamp"]
    entryprice = stock_status["entry_price"]
    slprice = stock_status["stop_loss"]
    target = stock_status["target"]

    parsed_datetime = datetime.fromisoformat(ts[:-6])  # Remove the timezone part for parsing
    hour = parsed_datetime.hour
    minute = parsed_datetime.minute

    if not (hour < 12 or (hour == 12 and minute < 59)):
        return 

    levels = fetchLevels(stock,scanday - timedelta(1) , tradetype, entryprice)
    start_time, end_time = maketimeframe(scanday, scanday)
    df = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, stock_token_mapping[stock], scanday, "FIVE_MINUTE",start_time, end_time, fetchlatest = True)
    if(df is not None):
        if(stock_status["telegram_notify"] == True):
            df = calcVWAP(df) 
            filename = backtest_save(stock, scanday, df, ts, slprice, entryprice, levels, color, foldertype, target)
            
            stock_text = "{} - {}".format(foldertype, stock)
            message = stock_text.upper() + " \n stop_loss : " + str(stock_status["stop_loss"]) + "\n" + "entry_price : " +  str(stock_status["entry_price"]) + "\n" + "target : " +  str( math.ceil(stock_status["target"] * 100) / 100)
            
            file = {'photo': open(filename,'rb')}
            stock_status["telegram_notify"] = False
            
            # sendmessage("------------- ALERT ------------------")
            # sendmessage(message)
            # sendphoto(file)
            with lock:
                day_maintainer[stock] = stock_status
                overall_maintainer[maintainerdaykey] = day_maintainer
                with open("daystatus.json", "w") as fout:
                    json.dump(overall_maintainer,fout)

            print(stock, " saved")




def scan(timeframe):
    folder = "./data/"+timeframe+"/"
    while(True):
        with lock:
            day_maintainer_copy = day_maintainer.copy()
            
        watchstocks = [stock for stock,details in day_maintainer_copy.items() if (details["watching"] == True and details["telegram_notify"] == True)]
        if(len(watchstocks)<=0):
            print("Empty Scan list")
            time.sleep(5)

        else:
            print()
        
        for stock in watchstocks: 
            try:
                stockstatus =  day_maintainer_copy[stock]    
                filename = folder + "{}/{}-{}-{}.csv".format(stock, scanday.day, scanday.month, scanday.year)
                if(not os.path.exists(filename)):
                    continue
                
                df = pd.read_csv(filename)
                df = calcVWAP(df)
                selection_pct = 1.5
                if(stock in ["TCS", "INFY", "RELIANCE","HDFCBANK", "ICICIBANK", "SBIN"]):
                    selection_pct = 1

                if(not stockstatus["is_entry_made"]):
                    if(stockstatus["is_above_sma"] is True ):
                        slprice, entryprice, tsindex, vwapprice = checkforbullish(df,stockstatus["lastdayclose"],stockstatus["lastdayhigh"], 30, selection_pct)
                        
                        if(slprice > 0):
                            ts = df.loc[tsindex,"timestamp"]
                            stockstatus["is_entry_made"] = True
                            stockstatus["stop_loss"] = slprice
                            stockstatus["entry_price"] = entryprice
                            stockstatus["target"] = entryprice + 2.5 * (entryprice - slprice)
                            stockstatus["entry_timestamp"] = ts
                            
                            processstock(stock, stockstatus)

                    if(stockstatus["is_above_sma"] is False):
                        slprice, entryprice, tsindex, vwapprice = checkforbearish(df, stockstatus["lastdayclose"], stockstatus["lastdaylow"], 30, selection_pct)
                        
                        if(slprice > 0):
                            ts = df.loc[tsindex,"timestamp"]
                            stockstatus["is_entry_made"] = True
                            stockstatus["stop_loss"] = slprice
                            stockstatus["entry_price"] = entryprice
                            stockstatus["target"] = entryprice - 2.5 * (slprice - entryprice)
                            stockstatus["entry_timestamp"] = ts
                            
                            processstock(stock, stockstatus)
                    
            except Exception as e:
                print("Error in scan thread bull", stock, "   " ,e)
                        
                        
# def aftermarket():
#     for stock, token in stock_token_mapping.items():
#         start_time, end_time = maketimeframe(scanday, scanday)
#         df = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, scanday, "ONE_MINUTE",start_time, end_time, fetchlatest = False)
#         if(df is not None):  
#             print(stock," download successful")          
#             if(stock not in possible_buys and stock not in possible_sells):
#                 if(equity_bull_stocks.get(stock) is not None):
#                     _, _, open, high, low, close, _ = stock_low_high_list[stock]
#                     price = df["high"].max()
#                     if price >= high:
#                         if(((price - close)/close)*100 > 1.4):
#                             with lock:
#                                 possible_buys.append(stock)

#                 if(equity_bear_stocks.get(stock) is not None):
#                     _, _, open, high, low, close, _ = stock_low_high_list[stock]
#                     price = df["low"].min()
#                     if price <= low:
#                         if(abs(((price - close)/close)*100) > 1.4):
#                             with lock:
#                                 possible_sells.append(stock)



t1 = threading.Thread(target=synclivestocks, args=(fetchobj, angleobj, scanday, "ONE_MINUTE",))
t1.start()

t2 = threading.Thread(target=scan, args=("ONE_MINUTE",))
t2.start()

threading.Thread(target=sws.connect(), args=()).start()
time.sleep(5)



time.sleep(10000)
# t1.join()


# print("thread has started")


