import json
import json
import datetime
from datetime import timedelta
import pandas as pd
import os

stock_token = {}
with open("../Info/stock_token_json.json", "r") as infile:
    stock_token = json.load(infile)

symboldf = pd.read_csv("../Info/ind_nifty200list.csv")
stocklist = symboldf["Symbol"].to_list()

def findToken(stock, mkr):
    for stockdetail in stock_token:
       if(stockdetail["symbol"] == stock + mkr):
          return stockdetail["token"]
    return
   
d = datetime.datetime.today()
timeframe = "ONE_MINUTE"

for day in range(1,2):
    initialday = d - timedelta(day)
    folder = "../data/"+timeframe+"/"
    for stock in symboldf["Symbol"].to_list():
        filename = folder + "{}/{}-{}-{}.csv".format(stock, initialday.day, initialday.month, initialday.year)   
        token = findToken(stock , "-EQ")
        if not token:
            print("unable to find the token")
            continue 

        if(os.path.exists(filename)):
            df = pd.read_csv(filename)
            print(len(df))
      
    
        

      
