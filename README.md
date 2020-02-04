# `NTex` - 新台幣匯率查詢

![image](https://img.shields.io/badge/python-3.7-blue.svg)

各國貨幣匯率 :參考[比率網](https://www.findrate.tw/)匯率資料

歷史黃金價格 : 參考[台灣銀行黃金存摺牌價](https://rate.bot.com.tw/gold/passbook?Lang=zh-TW)

# Quick Start

```python
from ExchangeRate import NTex

# 可用貨幣查詢 (中英對照)
NTex()._currencies()

# 今日所有匯率
NTex().now_all()

# 歷史黃金價格
NTex().gold()

# 目前黃金價格
NTex().gold_()

########################## 
#單一匯率應用 (美金為例)
USD = NTex(currency='USD')

# 目前各銀行匯率
USD.now()

# 近期新聞(顯示10筆)
USD.news()

# 近10年歷史匯率 (2010-now)
USD.history()

# 趨勢圖 (可設定起始時間)
USD.plot()

# 查詢單個年度匯率
USD._year(2020)
```
