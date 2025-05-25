import pandas as pd
# import os # os.chdir is environment-specific, removing for general use.
# Script assumes ExchangeRate.py is in the same directory or NTex is in PYTHONPATH

# 設定 pandas 顯示選項，以便更好地查看 DataFrame 輸出
pd.options.display.max_columns = 10
pd.options.display.width = 120 # 調整寬度以便顯示更多列數據

from ExchangeRate import NTex

# 測試基本功能：獲取可用幣別列表和所有幣別的即時匯率
print("獲取所有可用幣別的中文名稱及代碼...")
available_currencies = NTex()._currencies()
if available_currencies:
    print("可用幣別:", available_currencies)
else:
    print("未能獲取可用幣別列表。")

print("\n獲取所有幣別的即時匯率...")
all_now_rates = NTex().now_all()
if all_now_rates is not None and not all_now_rates.empty:
    print("所有幣別即時匯率 (前5筆):")
    print(all_now_rates.head())
else:
    print("未能獲取所有幣別的即時匯率。")

print("\n--- 開始示範各幣別的歷史匯率圖表 ---")
# 迭代一些主要幣別進行繪圖示範
# currencies_to_plot = ["USD", "JPY", "EUR", "CNY", "AUD"] # 可以選擇部分貨幣以節省時間
currencies_to_plot = NTex()._currencies().keys() if available_currencies else [] # 或者全部

for currency_code in currencies_to_plot:
    print(f"\n--- 正在處理幣別: {currency_code} ---")
    try:
        currency_trader = NTex(currency_code) # 創建對應幣別的 NTex 實例
        
        # 示範繪製標準歷史匯率圖 (例如從2021年開始)
        print(f"繪製 {currency_code} 從 2021 年開始的歷史匯率圖...")
        currency_trader.plot(target_year=2021) # 不顯示買入建議

        # 針對特定幣別 USD 和 JPY，示範顯示買入建議的功能
        if currency_code == "USD":
            print(f"繪製 {currency_code} 從 2021 年開始的歷史匯率圖 (包含買入建議)...")
            currency_trader.plot(target_year=2021, show_suggestions=True)
            
            print(f"繪製 {currency_code} 從 2022 年開始的歷史匯率圖 (包含買入建議，自訂參數)...")
            currency_trader.plot(target_year=2022, show_suggestions=True, window_size=15, std_multiplier=2.0)

        elif currency_code == "JPY":
            print(f"繪製 {currency_code} 從 2021 年開始的歷史匯率圖 (包含買入建議)...")
            currency_trader.plot(target_year=2021, show_suggestions=True)
            
    except Exception as e:
        print(f"處理幣別 {currency_code} 時發生錯誤: {e}")

# --- 示範直接調用 suggest_buying_rate 方法 ---
print("\n\n--- 示範直接獲取 USD 的買入建議數據 ---")
usd_analyzer = NTex("USD")
# 首先，需要獲取歷史數據才能進行分析
print("正在獲取 USD 的歷史數據以供分析...")
usd_history_data = usd_analyzer.history() # history() 會處理數據加載和存儲

if usd_history_data is not None and not usd_history_data.empty:
    print("USD 歷史數據已獲取。現在計算買入建議...")
    # 調用 suggest_buying_rate 方法
    usd_suggestion_df = usd_analyzer.suggest_buying_rate(
        currency_data=usd_history_data, # 使用剛獲取的歷史數據
        window_size=20, 
        std_multiplier=1.5
    )
    
    if usd_suggestion_df is not None and not usd_suggestion_df.empty:
        print("\nUSD 買入建議數據 (末10筆):")
        print(usd_suggestion_df.tail(10))
    else:
        print("未能成功生成 USD 的買入建議數據。")
else:
    print("未能獲取 USD 的歷史數據，無法進行買入建議分析。")


# --- 黃金數據處理示範 ---
print("\n\n--- 黃金數據處理示範 ---")
gold_handler = NTex() # 黃金功能不需指定幣別於初始化

print("獲取並繪製黃金歷史價格...")
gold_data = gold_handler.gold() # 預設 show_plot=True
if gold_data is not None and not gold_data.empty:
    print("黃金歷史數據 (末5筆):")
    print(gold_data.tail())
else:
    print("未能獲取黃金歷史數據。")

print("\n獲取目前黃金牌價...")
gold_handler.gold_now()

print("\n--- 範例腳本執行完畢 ---")