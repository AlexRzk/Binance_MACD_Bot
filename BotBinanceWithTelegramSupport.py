#!/usr/bin/env python
# coding: utf-8

# In[1]:


#import libraries

import pandas as pd
from binance.client import Client
import ta 
import time
import binance
import websocket
from binance.exceptions import BinanceAPIException 
from backtesting import Backtest, Strategy
from backtesting.lib import crossover 
import matplotlib.pyplot as plt
from IPython.display import clear_output
import json
from contextlib import closing
from websocket import create_connection
import requests


# In[2]:


#here i am defining my Binance API settings (it look like wfdieng375fhr...) 



api_key = ''
api_secret = ''

client = Client(api_key, api_secret)


# In[3]:


#Here is the loop that is checking the actual price of a cryptocurrency

def getactualprice(symbol):
    try:
        frame = pd.DataFrame(client.get_historical_klines(symbol, '1s', '5s'))
    except BinanceAPIException as e:
        print(e)
        sleep(3)
        frame = pd.DataFrame(client.get_historical_klines(symbol, '1s', '2min'))
    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit = 'ms')
    frame = frame.astype(float)
    return frame


# In[4]:


#Here is the actual price with an interval like 4 hours or others


def getHOURdata(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback+'h ago UTC'))
    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit = 'ms')
    frame = frame.astype(float)
    return frame


# In[5]:


#Here is the price with the interval of 2 hours

def get2Hdata(symbol):
    try:
        frame = pd.DataFrame(client.get_historical_klines(symbol, '2h', '96h ago UTC'))
    except BinanceAPIExeption as e:
        print(e)
        sleep(30)
        frame = pd.DataFrame(client.get_historical_klines('BTCUSDT', '2h', '8 h ago UTC'))
    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit = 'ms')
    frame = frame.astype(float)
    return frame


# In[6]:


#Indicator i am using for this bot, you can change the parameter for your own settings

def MACD(df):
    df['EMA12'] = df.Close.ewm(span=12).mean()
    df['EMA28'] = df.Close.ewm(span=28).mean()
    df['MACD'] = df.EMA12 - df.EMA28
    df['Signal'] = df.MACD.ewm(span=9).mean()
    df['Diff'] = df.MACD - df.Signal
    return df


# In[7]:


#Here is important things, you need to change this thing (grtbusd@kline_1m) for your crypto like for btcusdt it will be btcusdt@kline_1m
#this is checking price of a crypto without crashing due to the small interval of asking the price

socket = 'wss://stream.binance.com:9443/ws/grtbusd@kline_1m'



def convert(frame):
    
    json_message = json.loads(frame)
    candle = json_message['k']
    df = [1, 2, 3, 4, 5, 6]
    df[1] = float(candle['x'])
    df[2] = float(candle['c'])
    df[3] = float(candle['l'])
    df[4] = float(candle['h'])
    df[5] = float(candle['o'])
    return df

#Here you have the function that is sending a message to your telegram channel bot, the tutorial i used is there : https://builtin.com/software-engineering-perspectives/telegram-api
#def send_message(mess):
#    url = f'https://api.telegram.org/something_here/sendMessage?chat_id=chat_id={mess}'
#    requests.get(url)


#main loop for the bot
def strategy(symbol, qty, open_position = False, crossunder = False):
    while True:
        
        with closing(create_connection(socket)) as conn:
            
            actualpriceraw = conn.recv()
            actualprice = convert(actualpriceraw)
            
            
        strat = getHOURdata(symbol, '2h', '96')
        strat1 = MACD(strat)
        strat2 = strat1.tail(1)
        
        if not open_position:
            if not crossunder:
                time.sleep(120)
                strat3 = getHOURdata(symbol, '2h', '96')
                strat4 = MACD(strat3)
                strat5 = strat4.tail(1)
                if (strat2.MACD < (strat2.Signal)).all() and (strat5.MACD < (strat5.Signal)).all():
                    crossunder = True
                    print("cross under true")
                    print(strat2)
                    print(strat5)
                
            if (strat2.MACD > strat2.Signal).all() and crossunder:
                order = client.order_market_buy(symbol=symbol, quantity=qty)
                print(order)
                buy_price = float(order['fills'][0]['price'])
                print('Buy Price : ', buy_price)
                qty_buy_price = float(buy_price*qty)
                #uncomment this two lines if you are using the telegram bot
                #message1 = (f'ENTER LONG \nSymbol: {symbol} \nQuantity: {qty} \nQuantity Price: {qty_buy_price} \nEntry Price: {buy_price} \nStop Loss: -4%, {(buy_price*0.96)} \nTake Profit: 8%, {(buy_price*1.08)}')
                #send_message(message1)
                crossunder = False
                open_position = True
                
        
        if open_position:
            #here is the stop loss and the take profit to define
            if (actualprice[2] < (buy_price * 0.96)) or (actualprice[2] > (buy_price * 1.08)):
                order = client.order_market_sell(symbol=symbol, quantity=qty)
                print(order)
                sell_price = float(order['fills'][0]['price'])
                print('Sell Price : ', sell_price)
                print(f'profit = {(sell_price - buy_price)}'"$")
                profit = ((sell_price*qty)-(buy_price*qty))
                #uncomment this two lines if you are using the telegram bot
                #message2 = (f'CLOSE LONG \nSymbol: {symbol} \nQuantity: {qty} \nQuantity Price: {qty_buy_price} \nSell Price: {sell_price} \nProfit: {profit}')
                #send_message(message2)
                open_position = False


# In[8]:


strategy('GRTBUSD', qty = 300)
         




