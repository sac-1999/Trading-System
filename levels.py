import pandas as pd
import os
import datetime


def findlevels(df, window, leveltype):
    if(leveltype == "bullish"):
        df["is_resistance"] = df['high'].rolling(window=window, center=True).max()
        resistancelist = df[df["is_resistance"] == df['high']]["high"].to_list()
        if(len(resistancelist) == 0):
            return []

        lastresistance = resistancelist[-1]
        finalresistance = []
        for res in reversed(resistancelist):
            if(res >= lastresistance):
                finalresistance.append(res)
                lastresistance = res
        return finalresistance

    if(leveltype == "bearish"):
        df["is_support"] = df['low'].rolling(window=window, center=True).min()
        supportlist = df[df["is_support"] == df['low']]["low"].to_list()
        finalsupport = []

        if(len(supportlist)==0):
            return []

        lastsupport =  supportlist[-1]
        for sup in reversed(supportlist):
            if(sup<=lastsupport):
                lastsupport = sup
                finalsupport.append(sup)
        return finalsupport

# stock,token, scanday, entryprice, "bearish"

def fetchLevels(stock, scanday, type, entryprice):
    folder = "./data/ONE_DAY/"
    filename = folder + "{}/{}-{}-{}.csv".format(stock, scanday.day, scanday.month, scanday.year)
    finallevels = []
    if(os.path.exists(filename)):
        df = pd.read_csv(filename)
        finallevels.extend(findlevels(df,5,type))

    folder = "./data/ONE_HOUR/"
    filename = folder + "{}/{}-{}-{}.csv".format(stock, scanday.day, scanday.month, scanday.year)
    if(os.path.exists(filename)):
        df = pd.read_csv(filename)
        finallevels.extend(findlevels(df,9,type))

    finallevels = sorted(finallevels)
    if(type == "bullish"):
        finallevels = [level for level in finallevels if(level < entryprice + entryprice*0.025 and level > entryprice - entryprice*0.005)]

    else:
        finallevels = [level for level in finallevels if(level > entryprice - entryprice*0.025 and level < entryprice + entryprice*0.005)]

    return finallevels