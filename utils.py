import os
import pandas as pd
from savestockdata import downloadandsaveForBacktesting
import time
from datetime import datetime, timedelta
import json
from savetrade import backtest_save
from sklearn.linear_model import LinearRegression
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt


def calcVWAP(df):
    df['volume'] = df['volume'].astype(float)  # Ensure Volume is a float
    df['Cumulative Volume'] = df['volume'].cumsum()
    df['Cumulative Price x Volume'] = (df['volume'] * (df['open'] + df['high'] + df['low'] + df['close']) / 4).cumsum()
    df['VWAP'] = df['Cumulative Price x Volume'] / df['Cumulative Volume']
    return df

def findToken(stock, mkr, stock_token):
    for stockdetail in stock_token:
       if(stockdetail["symbol"] == stock + mkr):
          return stockdetail["token"]
    return

def maketimeframe(startday, endday):
    endtup = endday.timetuple()
    end_time = "{:04d}-{:02d}-{:02d} 15:30".format(endtup[0],endtup[1], endtup[2])
    starttup = startday.timetuple()
    start_time = "{:04d}-{:02d}-{:02d} 09:15".format(starttup[0],starttup[1], starttup[2])

    return start_time, end_time


def fetchLastdays(stock, scanday):
    folder = "./data/ONE_DAY/"
    filename = folder + "{}/{}-{}-{}.csv".format(stock, scanday.day, scanday.month, scanday.year)
    if(os.path.exists(filename)):
        df = pd.read_csv(filename)
        if len(df)>=1:
            row = df.iloc[-1]
            return tuple(row)
        
    return -1, -1, -1, -1, -1, -1, -1


def synclivemarket(fetchobj, angleobj,listofstocks, scanday, timeframe, iteration, backtest):
    start_time, end_time = maketimeframe(scanday, scanday)
    
    while(iteration > 0):
        if(backtest == True):
            iteration = iteration - 1

        failedcount = 0
        for stock, token in listofstocks.items():
            if(failedcount>10):
                break
            df = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, scanday, timeframe,start_time, end_time, fetchlatest = not backtest)
            if(df is None or len(df) == 0):
                print(stock, " unsuccessful sync ", scanday)
                failedcount = failedcount + 1
                continue
            else:
                print(stock, ": successfully fetched data for sync ", scanday)
              


def syncDailydata(fetchobj, angleobj, listofstock, endday):
    for stock, token in listofstock.items():
        start_time, end_time = maketimeframe(endday - timedelta(400), endday)
        downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, endday, "ONE_DAY", start_time, end_time, False)
        print(stock, " : Daily sink done ", endday.day)
        start_time, end_time = maketimeframe(endday - timedelta(60), endday)
        downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, endday, "ONE_HOUR", start_time, end_time, False)
        print(stock, " : Hour sink done ", endday.day)

  
def fetchLowHigh(fetchobj, angleobj, stock, token, endday):
    start_time, end_time = maketimeframe(endday - timedelta(400), endday)
    df = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, endday, "ONE_DAY", start_time, end_time, False)
    if(df is not None):
        return (df.tail(1)["low"].min(), df.tail(1)["high"].max())
    
    return(-1,-1)
        

def buildstockimage(fetchobj, angleobj, listofstock, endday):
    with open("daystatus.json", "r") as fin:
        allrecords = json.load(fin)
    
    for stock in listofstock:
        key = stock + "{}{}{}".format(endday.day, endday.month, endday.year)
        if allrecords.get(key) is not None:
            stockdayracord = allrecords[key]
            # print(stockdayracord)
            scanday = datetime.strptime(stockdayracord["day"], "%Y-%m-%dT%H:%M:%S.%f")
            if(stockdayracord["isnew"] is False):
                continue
            

            entryprice = stockdayracord["entryprice"]
            slprice = stockdayracord["slprice"]
            levels = stockdayracord["levels"]
            type = stockdayracord["type"]
            token = stockdayracord["token"]  
            timestamp = stockdayracord["timestamp"]
            allrecords[key]["isnew"] = False

            with open("daystatus.json", "w") as fout:
                json.dump(allrecords, fout)
            
            start_time, end_time = maketimeframe(scanday, scanday)
            df = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, scanday, "FIVE_MINUTE",start_time, end_time, fetchlatest = False)
            if(df is not None):
                df = calcVWAP(df) 
                levelcolor = "red" if type=="buy" else "green"      
                backtest_save(stock, scanday, df, timestamp, slprice, entryprice, levels, levelcolor, type)
                print(stock , " Trade saved for ", scanday.day)


def calculate_sma(data, window_size):
    return data.rolling(window=window_size).mean()


def slopefinder(df):
    df['Time'] = np.arange(len(df))
    model = LinearRegression()
    model.fit(df['Time'].values.reshape(-1, 1), df['sma'])
    slope = model.coef_[0]
    return slope


def checkPossibleStockForDay(stock, day_data, d):
    day_data["sma"] = calculate_sma(day_data['close'], 21)
    # day_data["11sma"] = calculate_sma(day_data['close'], 11)
    testdf = day_data.iloc[-1]
    if(testdf["close"] < testdf["sma"]):
        return False
    
    # if(testdf["close"] < testdf["11sma"]):
    #     return False
    
    # slope = slopefinder(day_data.tail(10))
    # if(slope < 0):
    #     return False
    
    # day_data['Date'] = pd.to_datetime(day_data['timestamp'])
    # day_data.set_index('Date', inplace=True)
    # ap = mpf.make_addplot(day_data['sma'], color='white', secondary_y=False, linewidths=0.1)
    # ap11 = mpf.make_addplot(day_data['11sma'], color='green', secondary_y=False, linewidths=1)
    # ap2 = mpf.make_addplot(day_data['volume'], panel=1)
    # fg,ax = mpf.plot(day_data, type='candle', style='mike', hlines={"hlines":[], "colors":[], "linestyle":[], "linewidths":[]},figratio=(40,20), returnfig=True, addplot=[ap,ap2, ap11],volume = True, title=stock, figscale=2)
    # ax[0].grid(False)

    # try:
    #     os.makedirs("dates/{}/{}/".format("swing",str(d.day) + str(d.month) + str(d.year)), exist_ok = True)
    #     plt.savefig("dates/{}/{}/{}.jpg".format("swing",str(d.day) + str(d.month) + str(d.year),stock))
        
    # except OSError as error:
    #     print("Directory '%s' can not be created")
    

    return True


def filterstock(fetchobj, angleobj, stock, token, scanday, smawindow):
    start_time, end_time = maketimeframe(scanday - timedelta(400), scanday)
    df = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, scanday, "ONE_DAY", start_time, end_time, False)
    if(df is not None):
        df["sma"] = calculate_sma(df['close'], smawindow)
        if(df.iloc[-1]["close"] > df.iloc[-1]["sma"]):
            return True

        elif(df.iloc[-1]["close"] <= df.iloc[-1]["sma"]):
            return False

    return None

