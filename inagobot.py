# -*-coding:utf-8-*-
import pybitflyer
from inago import InagoFlyer
import datetime as dt
import csv

inago = InagoFlyer()


# ユーザー定義
# --------------------------------#
AVG = 20  # 平均取得秒数
LOW = 30  # 不足しきい値
TIE = 30  # 引き分け判定しきい値
Position = 0  # 初期ポジション指定(0: No, 1: Buy, -1: Sell)
LOT = 0.01  # 1回のトレード枚数


KEY = ""  # APIキー
SECRET = ""  # APIシークレットキー
# BitFlyerの場合 (FX_BTC_JPY or BTC_JPY)
Pair = "BTC_JPY"
# --------------------------------#

# 変数初期化
Merit = None
api = pybitflyer.API(api_key=KEY, api_secret=SECRET)
value = 0
profit = 0
file = "./data.csv"
df = []
trade = []


def Market(side):
    global Position
    ret = api.sendchildorder(
        product_code=Pair,
        child_order_type="MARKET",
        side=side,
        size=LOT,
        minute_to_expire=10000,
        time_in_force="GTC",
    )
    if "child_order_acceptance_id" in ret:
        Position += 1 if Merit == "Buy" else -1
        print(ret["child_order_acceptance_id"])
    else:
        print(ret)
    return ret


def WriteTrade(Merit, Position, profit):
    file = "./trade.csv"
    global trade
    trade.append(
        [dt.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), Merit, Position, profit]
    )

    # ファイルに書く
    with open(file, "w") as f:
        writer = csv.writer(f)
        writer.writerows(trade)


# メインループ
for volume in inago.VolumeGet():
    # 価格の取得
    ticker = api.ticker()
    AskTick = ticker["best_ask"]
    BidTick = ticker["best_bid"]

    if dt.datetime.now().strftime("%S") == "00":
        df.append(
            [
                dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                Merit,
                Position,
                volume["Buy"],
                volume["Sell"],
                AskTick,
                BidTick,
                profit,
            ]
        )
        # ファイルに書く
        with open(file, "w") as f:
            writer = csv.writer(f)
            writer.writerows(df)

    # 売買勢力が変わった場合
    if volume["Merit"] != Merit:
        Merit = volume["Merit"]
        print(dt.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        print("{} (Position = {})".format(Merit, Position))
        print("\tBuyVolume: {}".format(volume["Buy"]))
        print("\tSellVolume:{}".format(volume["Sell"]))
        print("\tAsk:{}".format(AskTick))
        print("\tBid:{}".format(BidTick))

        # 売買勢力が拮抗
        if Merit == "Even":
            if volume["Buy"] > volume["Sell"]:
                if Position != 1:
                    if Position == -1:
                        print("\tProfit:{}".format(value - AskTick))
                        profit += value - AskTick
                        WriteTrade(Merit, Position, value - AskTick)
                    Position = 0
            else:
                if Position != -1:
                    if Position == 1:
                        print("\tProfit:{}".format(BidTick - value))
                        profit += BidTick - value
                        WriteTrade(Merit, Position, BidTick - value)
                    Position = 0

        # 売買勢力が買い
        if Merit == "Buy":
            # 利確または損切り
            if Position != 1:
                if Position == -1:
                    print("\tProfit:{}".format(value - AskTick))
                    profit += value - AskTick
                    WriteTrade(Merit, Position, value - AskTick)
                Position = 1
                value = AskTick

        # 売買勢力が売り
        elif Merit == "Sell":
            # 利確または損切り
            if Position != -1:
                if Position == 1:
                    print("\tProfit:{}".format(BidTick - value))
                    profit += BidTick - value
                    WriteTrade(Merit, Position, BidTick - value)
                Position = -1
                value = BidTick

        print("\tTotal:{}\n".format(profit))
