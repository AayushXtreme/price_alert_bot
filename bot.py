## Using unocoin api 

from requests import Response, Session
import requests, time
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from prettytable import PrettyTable
from datetime import datetime, timedelta
from playsound import playsound
import pandas as pd
import json, os


# update params
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
session = Session()
session.headers.update(headers)


## get request from the url  
def get(url, params=None):
    print("\n....Fetching Data From API .......")
    try:
        response = session.get(url, params=params)
        data = json.loads(response.text)
        if 'error' in data.keys():
            raise SystemExit(data['error'])
        else:
            return data
    # except
    except (ConnectionError, Timeout, TooManyRedirects) as err:
        print(err)
        print("\nTrying again after some time...")
        time.sleep(600)  ## after 10 minutes
        return get(url, params=params)


## customized price alerts
def alert(asset, old_price, new_price, time):
    table = PrettyTable(['Asset', 'Previous Value', 'New Value', 'Last Updated'])
    old_price = 'INR ' + str(old_price)
    new_price = 'INR ' + str(new_price)
    table.add_row([asset, old_price, new_price, time])
    
    ## getting play sound
    print("\nPrice update")
    print(table)
    file = 'alert.wav'
    file = os.path.abspath(file)
    try:
        playsound(file)
    except:                                                                                                                                                                                                                                          
        ts = f'termux-notification -t "{asset} {new_price}"'                                   
        os.system(ts) 


## saving data and finishing changes
def save(df, file='alerts.csv'):
    print("\nSaving the data...")
    df.to_csv(file, index=False)
    print("Done.")
    ## update the file in cloud


def main(url, df, coin='BTC', wait=5):
    try:
        ## time loop 
        while True:
            # api request
            json = get(url)
            now = datetime.now()
            
            # prices
            print("\nComparing prices...")
            old_price = float(df.loc[df['coin']==coin].iloc[-1]['price(inr)'])
            new_price = float(json[coin]['buying_price'])

            # prices compare
            if new_price > old_price:
                alert(coin, old_price, new_price, now.strftime("%Y-%m-%d %H:%M:%S"))
            
            # updating data
            data = {'coin': coin, 'price(inr)': new_price, 'last_updated': now.strftime("%Y-%m-%d %H:%M:%S")}
            df = df.append(data, ignore_index=True)
            
            # Api update after desired minutes
            print("===============================")
            print(f'API refreshes every {wait} minute')
            future = now + timedelta(minutes=wait)
            print("Next Update on {}".format(future.strftime("%H:%M:%S")))
            print("================================")
            time.sleep(wait*60)

    except KeyboardInterrupt:
        save(df)
    except:
        print("\nSome error occurred!!!")
        save(df)
        

url = 'https://api.unocoin.com/api/trades/in/all/all'
payload = {}
files = []
prices = pd.read_csv('alerts.csv')
main(url, prices)
