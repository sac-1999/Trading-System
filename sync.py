import requests
import json
import pandas as pd
from levels import findlevels
import os
import datetime

class allsyncstatus:
    def __init__(self, syncday, daywindow, hourwindow):
        self.day = syncday
        self.daykey = "{}-{}-{}".format(syncday.day, syncday.month, syncday.year)
        self.statusfilename = "sync.json"
        self.tokenfilename = "token.json"
        self.levelsfilename = "level.json"
        self.url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        self.daywindow = daywindow
        self.hourwindow = hourwindow
        self.stocktokendict = {}

        syncjson = open(self.statusfilename,"r")
        syncstatus = json.load(syncjson)
    
        if(syncstatus.get("syncday") is None or  syncstatus.get("syncday") != self.daykey):
            json_file = open(self.statusfilename, 'w')
            data = {"syncday" : self.daykey,
                    "dailysync": 0,
                    "tokensync": 0,
                    "levelsync": 0
                  }
            json.dump(data, json_file, indent=4)

        if os.path.exists(self.levelsfilename):
            with open(self.levelsfilename, "w") as f:
                json.dump({}, f, indent=4)
            

    def loadstatus(self):
        syncjson = open(self.statusfilename,"r")
        syncstatus = json.load(syncjson)
        return syncstatus
    
    def tokensync(self):
      
        syncstatus = self.loadstatus()
        if(syncstatus["tokensync"]==1):
            return
        response = requests.get(self.url, headers=self.headers)
        if response.status_code == 200:
          with open(self.tokenfilename, 'wb') as f:
            f.write(response.content)
        
          with open(self.statusfilename, "w") as f:
              syncstatus["tokensync"] = 1
              json.dump(syncstatus, f, indent=4)

          print(f"File '{self.tokenfilename}' has been downloaded successfully.")
        else:
          print("Sync failed for {}   {}".format(self.tokenfilename, response.status_code))


    def levelsync(self, stock, df_day, df_hour):
        if(len(df_day)<1 or len(df_hour)<1):
            return False
        levelfile = open(self.levelsfilename,"r")
        levels = json.load(levelfile)
        key = "{}_{}".format(stock, self.daykey)
        if(levels.get(key) is not None):
            return
        data = {}
        data["resistance"] = {}
        data["support"] = {}
    
        data["resistance"]["DAY"] = findlevels(df_day,self.daywindow,"bullish")
        data["support"]["DAY"] = findlevels(df_day,self.daywindow,"bearish")
        data["resistance"]["HOUR"] = findlevels(df_hour,self.hourwindow,"bullish")
        data["support"]["HOUR"] = findlevels(df_hour,self.hourwindow,"bearish")

        levels[key] = data
        with open(self.levelsfilename, "w") as f:
              json.dump(levels, f, indent=4)

        return True





        
       

    
