## Using unocoin api 

from requests import Request, Session
import requests, time
from requests.api import head
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


# Authentication key
# **CHANGE**
token = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS51bm9jb2luLmNvbS9hcGkvYXBpRG9jIiwiaWF0IjoxNjEwNDY2ODQ3LCJleHAiOjE2NDIwMDI4NDcsIm5iZiI6MTYxMDQ2Njg0NywianRpIjoiaU83eWhTN01JZ1NGamFZNyIsInN1YiI6MTI2NTg5MywiaW4iOiI0MmVlZjJiODVmZTc4NDY3YzcwZmU1NGNkZjJjMjAxMTM5MjQwN2UwYTE3NTU1YmRlZWY1MzdmMmE0NjBlOWNmIn0.OZWxubyEu6H7l__eV6TExy67CEwdmVD7iwBmsFxjlPA'


## function run once wrapper
def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper


## get request from the url  
def get(url, headers=None):
    try:
        response = session.get(url, headers=headers)
        data = json.loads(response.text)
        if 'error' in data.keys():
            raise SystemExit(data['error'])
        else:
            return data

    # except
    except (ConnectionError, Timeout, TooManyRedirects) as err:
        print(err)
        print("\nTrying again after some time...")
        time.sleep(300)  ## after 5 minutes
        return get(url, headers=headers)


## post request to the api 
def post(url, data, headers=None):
    try:
        ## prepared requests 
        req = Request('POST', url, data=data, headers=headers)
        prepped = req.prepare()
        resp = session.send(prepped)
        data = resp.json()
        if 'error' in data.keys():
            raise SystemExit(data['error'])
        else:
            return data

    # except
    except (ConnectionError, Timeout, TooManyRedirects) as err:
        print(err)
        print("\nTrying again after some time...")
        time.sleep(300)  ## after 5 minutes
        return post(url, data=data, headers=headers)


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


## get your crypto balance
def balance(coin):
    wallets = get('https://api.unocoin.com/api/wallet/', headers={'Authorization': token})['wallets']
    for i in wallets:
        if i['coin'] == coin:
            return i


## current rate of the coin 
def current_rate(coin, amt=0, action='sell'):
    price_json = get('https://api.unocoin.com/api/trades/in/all/all')[coin]
    price = fee = tax = total_amt = 0

    ## for selling
    if action.lower() == 'sell':
        price = float(price_json['selling_price'])
        fee = float(price_json['selling_price_fee'])
        tax = float(price_json['selling_price_tax'])
        coin_fee = (fee/100)*amt
        total_amt = round(amt - (coin_fee + (tax/100)*coin_fee), 2)
    ## for buying
    elif action.lower() == 'buy':
        price = float(price_json['buying_price'])
        fee = float(price_json['buying_price_fee'])
        tax = float(price_json['buying_price_tax'])
        coin_fee = (fee/100)*amt
        total_amt = round(amt + (coin_fee + (tax/100)*coin_fee), 2)
    return {'coin': coin, 'btc_value': float(amt / price), 'inr_value': amt, 'fee': fee, 'tax': tax, 'exchange_rate': price, 'total_amount': total_amt}


## saving data and finishing changes
def save(df, file='prices.csv'):
    print("\nSaving the data...")
    df.to_csv(file, index=False)
    print("Done.")
    ## update the file in cloud


## buying and selling crypto  
@run_once
def transaction(payload, action='sell'):
    if action.lower() == 'sell':
        res = post('https://api.unocoin.com/api/trading/sell-btc', headers={'Authorization': token}, data=payload)
        print(res)
    elif action.lower() == 'buy':
        res = post('https://api.unocoin.com/api/trading/buy-btc', headers={'Authorization': token}, data=payload)
        print(res)        
    print("\nWallet balance...")
    print(payload['coin'] + ' ' + balance(payload['coin'])['balance'])
    print('INR' + ' ' + balance('INR')['balance'])    



def bot(coin='BTC', wait=5, trade_instructions=None):
    print("\n....Fetching Data From API .......")

    # historical stored coin prices
    df = pd.read_csv('prices.csv')
    try:
        ## time loop 
        while True:
            now = datetime.now()
            # get the coin info
            price_json = current_rate(coin)
            
            # prices
            print("\nComparing prices...")
            old_price = float(df.loc[df['coin']==coin].iloc[-1]['price(inr)'])
            new_price = float(price_json['exchange_rate'])

            # prices compare
            if new_price > old_price:
                alert(coin, old_price, new_price, now.strftime("%Y-%m-%d %H:%M:%S"))
            
            # updating data
            data = {'coin': coin, 'price(inr)': new_price, 'last_updated': now.strftime("%Y-%m-%d %H:%M:%S")}
            df = df.append(data, ignore_index=True)

            # trading activities
            if trade_instructions is not None:
                for trigger in trade_instructions:
                    min, max = trigger['trigger_range'][0], trigger['trigger_range'][1]
                    payload = current_rate(trigger['coin'], amt=trigger['value'], action=trigger['action'])
                    if payload['exchange_rate'] > min and payload['exchange_rate'] < max:    # verify coin 
                        transaction(payload, action=trigger['action'])
            
            
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
        

triggers = [{
    'coin': 'ETH',
    'trigger_range': [90000, 120000],
    'action': 'sell',
    'value': 100
}, 
{
    'coin': 'BTC',
    'trigger_range': [2500000, 3000000],
    'action': 'sell',
    'value': 100
}]

bot(coin='BTC', trade_instructions=None)

