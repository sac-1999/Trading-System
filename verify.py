from sync import allsyncstatus
import pandas as pd
import json
from savestockdata import downloadandsaveForBacktesting
from anglecreds import angleone
import json
import datetime
from datetime import timedelta
from fetchdata import fetchdata

angleobj = angleone()
fetchobj = fetchdata(3,1000)

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


syncobj = allsyncstatus(datetime.datetime.today(), 5, 9)
syncobj.tokensync()
scanday = datetime.datetime.today()



def findToken(stock, tokendict, mkr):
    for stockdetail in tokendict:
       if(stockdetail["symbol"] == stock + mkr):
          return stockdetail["token"]
    return

def maketimeframe(startday, endday):
    endtup = endday.timetuple()
    end_time = "{:04d}-{:02d}-{:02d} 15:30".format(endtup[0],endtup[1], endtup[2])
    starttup = startday.timetuple()
    start_time = "{:04d}-{:02d}-{:02d} 09:15".format(starttup[0],starttup[1], starttup[2])

    return start_time, end_time


symboldf = pd.read_csv("./Info/ind_nifty200list.csv")
stocklist = symboldf["Symbol"].to_list()

stocktoken = open("token.json", "r")
tokendict = json.load(stocktoken)

for stock in stocklist:
    token = findToken(stock , tokendict,  "-EQ")
    if not token:
        print("unable to find the token")
        continue
    
    levelsday = scanday - datetime.timedelta(1)
    start_time, end_time = maketimeframe(levelsday - timedelta(400), levelsday)
    df_day = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, levelsday, "ONE_DAY", start_time, end_time, True)

    
    levelsday = scanday - datetime.timedelta(1)
    start_time, end_time = maketimeframe(levelsday - timedelta(30), levelsday)
    df_hour = downloadandsaveForBacktesting(fetchobj, angleobj.smartapi, stock, token, levelsday, "ONE_HOUR", start_time, end_time, True)

    if(not syncobj.levelsync(stock, df_day, df_hour)):
        print("levels missing for : ", stock)
    else:
        print("levels successfull for : ", stock)
    