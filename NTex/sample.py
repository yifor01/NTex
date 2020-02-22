import os
import pandas as pd
pd.options.display.max_columns = 10
os.chdir(r'D:\jobs\exchange_rate\NTex\NTex')
from ExchangeRate import NTex

QQ = NTex()._currencies()
NTex().now_all()

for cur in NTex()._currencies().keys():
    try:
        CUR = NTex(cur)
        CUR.plot(2020)
    except:
        print('error:',cur)

QQ = NTex()
QQ.gold()
QQ.gold_now()