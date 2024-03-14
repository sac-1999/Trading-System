import pandas as pd
import os
import datetime

def downloadandsaveForBacktesting(fetchobj, smartapi, stock, token, day, timeframe, start_time, end_time,  fetchlatest):
    folder = "data/"+timeframe+"/"
    filename = folder + "{}/{}-{}-{}.csv".format(stock, day.day, day.month, day.year)
    try:
      if(not fetchlatest):
        
        if(os.path.exists(filename)):
          df = pd.read_csv(filename)
          ts = df.loc[len(df)-1,"timestamp"]       
          ts = datetime.datetime.fromisoformat(ts).time()
          orgts = datetime.datetime.strptime("15:15:00", "%H:%M:%S").time()
          return df

          if( ts >= orgts):
              return df
          
      
      history_data = fetchobj.fetch(smartapi,"NSE", token, stock,start_time, end_time, timeframe)
      if history_data is not None:
        os.makedirs(folder + "{}/".format(stock), exist_ok = True)
        df = pd.DataFrame(history_data["data"], columns = ["timestamp", "open", "high", "low", "close", "volume"])
        df.to_csv(filename)  
        return df
      
      else:
        print("Can not fetch data for stock", stock)
        
        
    except OSError as error:
      print("Directory '%s' can not be created")

    except Exception as e:
      print("Logout failed: {}".format(str(e)))


