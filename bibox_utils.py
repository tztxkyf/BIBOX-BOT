# useful functions
# reference: https://biboxcom.github.io/v3/spot/zh/#api-2
# based on bibox api v3
# original api is JAVA, here rewrite in python

import requests
import json
import time
import hmac
import hashlib
import datetime  
import time
import sys
import hmac
import hashlib
import math
import statistics

api_key = "850db2b3132043010d36c02c0c2da2e34513d06a"
api_secret = "69ac1295a68ce8450f02d4a2b2be96710fce0ba5"

def get_timestamp():
    timestamp = time.time()
    timestamp = int(round(timestamp*1000))
    return timestamp

def get_md5(key, data):
    enc_res = hmac.new(key.encode('utf-8'), data.encode('utf-8'), hashlib.md5).hexdigest()
    return enc_res

def internet_check():
    # 网络测试
    url = "https://api.bibox.com/v3/mdata/ping"
    r = requests.get(url)
    print(r.json())
    if r.json()["state"] == 0:
        return "connection successful"
    return r["msg"]


def request_pairlist():
    # 查询交易对
    url = "https://api.bibox.com/v3/mdata/pairList"
    r = requests.get(url)
    r = r.json()
    if r["state"] == 0:
        return r["result"]
    return r["msg"]

def request_tradelimit():
    # 查询交易限制
    url = "https://api.bibox.com/v3.1/orderpending/tradeLimit"
    r = requests.get(url)
    r = r.json()
    if r["state"] == 0:
        return r["result"]
    return r["msg"]


def request_ticker(pair="BTC_USDT"):
    # ticker
    url = "https://api.bibox.com/v3/mdata/ticker?pair=%s" % (pair)
    # print(url)
    r = requests.get(url)
    r = r.json()
    # print(r)
    if r["state"] == 0:
        return r["result"]
    return r["msg"]

def get_values(r):
    t = [x["datetime"] for x in r]
    o = [float(x["open"]) for x in r]
    h = [float(x["high"]) for x in r]
    l = [float(x["low"]) for x in r]
    c = [float(x["close"]) for x in r]
    v = [float(x["vol"]) for x in r]
    return (t, o, h, l, c, v)

def request_kline(pair="BTC_USDT", period="15min", size=20):
    # 查k线
    url = "https://api.bibox.com/v3/mdata/kline?pair=%s&period=%s&size=%s" % (pair, period, str(size))
    print(url)
    r = requests.get(url)
    r = r.json()
    # print(r)
    if r["state"] == 0:
        for x in r["result"]:
            x["datetime"] = datetime.datetime.fromtimestamp(x["time"]/1000)
        return r["result"]
    return r["msg"]

def request_coin_asset():
    # 查询币币账户
    url = "https://api.bibox.com/v3.1/spot/account/assets"
    param = {"select": 1}
    ts = str(get_timestamp())
    param = {"select": 1}
    strParam  = json.dumps(param).replace(" ","")
    strToSign = '' + ts + strParam
    sign = get_md5(api_secret, strToSign)
    # print(ts, strParam, strToSign, sign)
    r = requests.post(
        url = url,
        headers={
            'content-type': 'application/json',
            'bibox-api-key': api_key,
            'bibox-api-sign': sign,
            'bibox-timestamp': ts,
        },
        data = strParam,
    )
    r = r.json()
    # print(r)
    if r["state"] == 0:
        return r["result"]
    return r["msg"]


def request_pending_orders(pair = "BTC_USDT"):
    # 查询当前订单
    url = "https://api.bibox.com/v3.1/orderpending/orderPendingList"
    param = {
        "pair": pair,
        "account_type": 0,
        "page": 1,
        "size": 10}
    ts = str(get_timestamp())
    strParam  = json.dumps(param).replace(" ","")
    strToSign = '' + ts + strParam
    sign = get_md5(api_secret, strToSign)
    r = requests.post(
        url = url,
        headers={
            'content-type': 'application/json',
            'bibox-api-key': api_key,
            'bibox-api-sign': sign,
            'bibox-timestamp': ts,
        },
        data = strParam,
    )
    r = r.json()
    if r["state"] == 0:
        return r["result"]
    return r["msg"]

def request_cancel_order(order_id):
    # 撤单
    url = "https://api.bibox.com/v3.1/orderpending/cancelTrade"
    param = {
        "orders_id":order_id,
    }
    ts = str(get_timestamp())
    strParam  = json.dumps(param).replace(" ","")
    strToSign = '' + ts + strParam
    sign = get_md5(api_secret, strToSign)
    r = requests.post(
        url = url,
        headers={
            'content-type': 'application/json',
            'bibox-api-key': api_key,
            'bibox-api-sign': sign,
            'bibox-timestamp': ts,
        },
        data = strParam,
    )
    r = r.json()
    if r["state"] == 0:
        return r["result"]
    return r["msg"]

def request_cancel_all_orders():
    # 撤销所有单子
    pending_orders =request_pending_orders()
    print("pending orders before cancel:", pending_orders)
    for order in pending_orders["items"]:
        print(order["id"])
        order_id = order["id"]
        r = request_cancel_order(order_id)
        print("try to cancel order,", order_id, "and server returns", r)
    pending_orders =request_pending_orders()
    print("pending orders after cancel:", pending_orders)
    
order_side_index = {"buy":1, "bid":1, "sell":2, "ask":2}

def request_add_order(pair, order_side, price, amount):
    # 下单
    url = "https://api.bibox.com/v3.1/orderpending/trade"
    param = {
        "pair": pair,
        "account_type": 0,
        "order_side": order_side_index[order_side],
        "order_type": 2,
        "price": price,
        "amount": amount,
     }
    print("add order", param)
    if (amount == 0):
        print("size too small")
        return
    ts = str(get_timestamp())
    strParam  = json.dumps(param).replace(" ","")
    strToSign = '' + ts + strParam
    sign = get_md5(api_secret, strToSign)
    r = requests.post(
        url = url,
        headers={
            'content-type': 'application/json',
            'bibox-api-key': api_key,
            'bibox-api-sign': sign,
            'bibox-timestamp': ts,
        },
        data = strParam,
    )
    r = r.json()
    if r["state"] == 0:
        return r["result"]
    return r["msg"]

def round_size(x, n = 4):
    y = 10**n
    return math.floor(x*y)/y

def round_price(x, n = 1):
    return round(x, n)
