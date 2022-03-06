# sample strategy 1
# - trade btc_usd pair
# - refresh every 15 minutes
# - place a bid order at lower bollinger line and an ask order at upper bollinger line
# - on average will keep half cash and half coin
# - it's a low-frequency market making strategy
# - to prevent a momentum trend from hurting the pnl, the cash and coins will be split into m slices, each interval only trade at most one slice.


# Load libs and check internet
from bibox_utils import *

def all_in_one():
    print("-"*20)
    # initialization and check internet
    print("current time is:", get_timestamp())
    print("current datetime is:", datetime.datetime.now())
    print("internet check:", internet_check())
    # print(request_tradelimit())
    rt =  request_ticker()
    print("ticker price:", rt)
    close = float(rt["last"])
    print("close:", close)

    # Define Constants
    m = 3 # number of slices on each side
    r_coin = 0.5 # ratio of coin vs total value
    r_cash = 0.5 # ratio of cash vs total value
    r_coin_slice = r_coin/m
    r_cash_slice = r_cash/m
    trading_pair="BTC_USDT"
    assets = trading_pair.split("_")
    coin_name = assets[0]
    cash_name = assets[1]
    kline_period="15min"
    width_bollinger = 2 # width of bolliger band
    bps = 0.00075 # trading bps
    print("parameters:", m, r_coin, r_cash, round(r_coin_slice, 3), round(r_cash_slice, 3),\
          trading_pair, assets, kline_period, width_bollinger, bps)

    # cancel all orders
    print("trying to cancel all orders")
    request_cancel_all_orders()

    # Get acount asset status
    print("trying to get acount asset status")
    asset_details = {}
    coin_asset = request_coin_asset()
    print(coin_asset)
    for x in coin_asset:
        if ("total" in x):
            print(x, coin_asset[x])
    for x in coin_asset["assets_list"]:
        if "coin_symbol" in x:
            if float(x["balance"]) > 0:
                print("coin: %s, balance: %s, USD value:: %s" % (x["coin_symbol"], x["balance"], x["USDValue"]))
            if x["coin_symbol"] in assets:
                asset_details[x["coin_symbol"]] = x
    print(asset_details)

    v_cash = float(asset_details[cash_name]["USDValue"])
    v_coin = float(asset_details[coin_name]["USDValue"])
    v = v_cash + v_coin
    print("total value: %f, cash %s value: %f, coin %s value: %f, fair value is:%f" % \
          (v, cash_name, v_cash, coin_name, v_coin, (v/(close**0.5))))

    # request kline
    # request_kline(pair="BTC_USDT", period="15min", size=20)
    start_time = time.time()
    r = request_kline(pair=trading_pair, period=kline_period, size=30)
    print(r[-1])
    (t, o, h, l, c, vol) = get_values(r)
    end_time = time.time()
    print("time consumed %f seconds" % (end_time-start_time))
    print("last close:", c[-1], "close vector:", c)

    sma =statistics.mean(c[len(c)-20:len(c)])
    std = statistics.stdev(c[len(c)-20:len(c)])
    b_l = sma - std * width_bollinger
    b_h = sma + std * width_bollinger

    sma_d1 =statistics.mean(c[len(c)-20-1:len(c)-1])
    std_d1 = statistics.stdev(c[len(c)-20-1:len(c)-1])
    b_l_d1 = sma_d1 - std_d1 * width_bollinger
    b_h_d1 = sma_d1 + std_d1 * width_bollinger

    print(sma, std, b_l, b_h)
    print(sma_d1, std_d1, b_l_d1, b_h_d1)

    close = c[-1]

    bid_prc = min(b_l, b_l_d1, c[-1])*(1-bps)
    ask_prc = max(b_h, b_h_d1, c[-1])*(1+bps)
    print(bid_prc,ask_prc)

    bid_size = min(v*r_cash_slice, v_cash)
    ask_size = min(v*r_coin_slice, v_coin)

    if v_cash > v * r_cash:
        bid_size = v_cash - v*r_cash + v*r_cash_slice

    if v_coin > v * r_coin:
        ask_size = v_coin - v*r_coin + v*r_coin_slice

    print(bid_size, ask_size)

    # place order
    prc = round_price(bid_prc)
    coin_size = round_size(bid_size/close) # not for sell, use close to convert size to coin size
    cash_size = coin_size * prc
    print("bid order, price %f, coin size %f, cash size %f", prc, coin_size, cash_size)
    r = request_add_order("BTC_USDT", "buy", prc, coin_size)
    print(r)
    time.sleep(1)

    prc = round_price(ask_prc)
    coin_size = round_size(ask_size/prc) # note for buy, use the offer price to convert size
    cash_size = coin_size * prc

    print("ask order, price %f, coin size %f, cash size %f", prc, coin_size, cash_size)
    r = request_add_order("BTC_USDT", "sell", prc, coin_size)
    print(r)
    time.sleep(1)
    print(request_pending_orders())


if __name__ == "__main__":
    condition = True
    while condition == True:
        if (datetime.datetime.now().minute % 15 == 0): # run every 15 minutes
            print("current datetime is:", datetime.datetime.now(), "start to run strategy, details see log.")
            all_in_one()
            time.sleep(60) # to wait for another minute
        print("current datetime is:", datetime.datetime.now(), " wait...")
        time.sleep(10) # check every few seconds
        
