def checkforbearish(df, lastdayclose, lastlow, window, pctfilter):
    
    min_price_to_trade = lastdayclose - (lastdayclose * pctfilter)/100
    entry_price = -1
    ts = ""
    df["is_neck"] = df['low'].rolling(window=window, center=True, min_periods=int(window*0.6), closed = "both").min()
    w_neck = df[df["is_neck"] == df['low']].index

    for necktop in w_neck:
      entry_price = df.loc[necktop,"low"]
      if(entry_price > min_price_to_trade):
         continue
      if(entry_price <= df.loc[:necktop,"low"].min() and entry_price <= lastlow):
          for i in df.loc[necktop+1:,:].index:
             currprice = df.loc[i, "low"]
             if(currprice<entry_price):

                ts = i
                newdf = df.loc[necktop:i,:].copy()
                newdf["is_top"] = newdf['high'].rolling(window=int(window*0.6), center=True, min_periods=int(window*0.5), closed = "both").max()
                sllistindex = newdf[newdf["is_top"] == newdf['high']]["high"].index
                heighestsl = entry_price
                sli = -1
                for slneckindex in sllistindex:
                   slprice = df.loc[slneckindex,"high"]
                   if(slprice > heighestsl):
                      heighestsl = slprice
                      sli = slneckindex
                      
                if(heighestsl > entry_price and sli != -1):
                    slprice = df.loc[sli,"high"]
                    vwapprice = df.loc[sli,"VWAP"]
                    return slprice, entry_price, ts, vwapprice
                    
                return -1, entry_price, ts, 0
    return -1, entry_price, ts, 0


def checkforbullish(df, lastdayclose, lasthigh, window, pctfilter):

    min_price_to_trade = lastdayclose + (lastdayclose * pctfilter)/100
    entry_price = -1
    ts = ""
    df["is_neck"] = df['high'].rolling(window=window, center=True, min_periods=window//2,closed = "both").max()
    w_neck = df[df["is_neck"] == df['high']].index
    
    for necktop in w_neck:
      entry_price = df.loc[necktop,"high"]
      if(entry_price < min_price_to_trade):
         continue
      if(entry_price >= df.loc[:necktop,"high"].max() and entry_price >= lasthigh):
          for i in df.loc[necktop+1:,:].index:
             currprice = df.loc[i, "high"]
             if(currprice>entry_price):
                ts = i
                newdf = df.loc[necktop:i,:].copy()
                newdf["is_bottom"] = newdf['low'].rolling(window=int(window*0.6), center=True, min_periods=window//2).min()
                sllistindex = newdf[newdf["is_bottom"] == newdf['low']]["low"].index
                lowestsl = entry_price
                sli = -1
                for slneckindex in sllistindex:
                   slprice = df.loc[slneckindex,"low"]
                   if(slprice < lowestsl):
                      lowestsl = slprice
                      sli = slneckindex
                      
                if(lowestsl < entry_price and sli != -1):
                    slprice = df.loc[sli,"low"]
                    vwapprice = df.loc[sli,"VWAP"]
                    return slprice, entry_price, ts, vwapprice
                    
                return -1, entry_price, ts, 0
    return -1, entry_price, ts, 0
