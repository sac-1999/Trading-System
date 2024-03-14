###fetch data class
import pandas as pd
from datetime import datetime
import time

def convertToDataframe(response):

        df = pd.DataFrame(response["data"], columns = ["timestamp", "open", "high", "low", "close", "volume"])
        return df


class RateLimitedMethod:
    def __init__(self, limit, per_millisecond):
        self.limit = limit
        self.per_millisecond = per_millisecond
        self.call_count = 0
        self.last_called = None

    def _reset_count(self):
        self.call_count = 0

    def _update_last_called(self):
        self.last_called = time.time()

    @property
    def can_call(self):
        current_time = time.time()
        if not self.last_called or current_time - self.last_called > self.per_millisecond/1000:
            self._reset_count()
        return self.call_count < self.limit


class fetchdata(RateLimitedMethod):
    def __init__(self, limit, per_millisecond):
        super().__init__(limit, per_millisecond)

    def fetch(self, smartApi, exchange, tokenofstock, stock, start_time, end_time, time_frame):
        history_data = {}
        try:
            if self.can_call:
                historicParam={
                "exchange": exchange,
                "symboltoken": tokenofstock,
                "interval": time_frame,
                "fromdate": start_time,
                "todate": end_time}

                
                history_data = smartApi.getCandleData(historicParam)
                
                if(history_data.get("data") is not None):
                    self.call_count += 1
                    self._update_last_called()

                else:
                    print("failed for : ",stock, "   ", history_data, "   ", historicParam)
                    pass


            else:
                t = time.time()
                wait_time = self.per_millisecond / 1000  - (t - self.last_called)
                if wait_time > 0:
                    time.sleep(wait_time)
                    return self.fetch(smartApi, exchange, tokenofstock, stock, start_time, end_time, time_frame)
            
        except Exception as e:
            print("fetch_day_data :: Historic Api failed: {} retrying",format(e) )
        
        if(history_data.get("data") is not None):
            return history_data
        
        return None

