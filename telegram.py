
import requests
import json


def telegramdetails():
  f = open("./Creds/creds.json", "r")
  dict = json.load(f)
  return (dict["telegram"]["token"], dict["chatid"])
  

def sendmessage( message ):
  token, chatid = telegramdetails()
  sendmessageurl = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chatid}&text={message}"
  res = requests.post(sendmessageurl).json()
  print(res)

def sendphoto( file ):
  token, chatid = telegramdetails()
  photourl = f"https://api.telegram.org/bot{token}/sendPhoto?chat_id={chatid}"
  res = requests.post(photourl, files = file).json()
  print(res)
