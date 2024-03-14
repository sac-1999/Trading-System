
##angle one account
import json
from SmartApi import SmartConnect
import pyotp


class angleone:

    def __init__(self):
        self.clientid = ""
        self.apikey = ""
        self.smartapi = ""
    

    def loadConf(self,file_name):
        dict = {}
        with open(file_name, "r") as file:
            dict = json.load(file)

        return dict

    def createSmartSession(self, dict, token):
        self.apikey = dict["api_key"]
        self.clientid = dict["clientId"]
        pwd = dict["pin"]
        self.smartapi = SmartConnect(self.apikey)
        
        totp=pyotp.TOTP(token).now()
        session = self.smartapi.generateSession(self.clientid, pwd, totp)
        return session


    def connect(self):
        dict = self.loadConf("./Creds/creds.json")
        session = self.createSmartSession(dict["historical"], dict["angletoken"])
        return session
    
    def terminate(self):
        try:
            logout=self.smartapi.terminateSession(self.clientid)
            print("Logout Successfull")
        except Exception as e:
            print("Logout failed: {}".format(str(e)))