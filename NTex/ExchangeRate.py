import requests
import datetime
import glob
import os
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

if not os.path.exists('data'):
    os.makedirs('data')


class NTex(object):
    def __init__(self, currency="USD"):
        """
        NTex 類別初始化。

        Args:
            currency (str): 要操作的目標貨幣代碼，預設為 "USD" (美金)。
                            對於黃金相關操作，此參數在初始化時不敏感。
        """
        self.currency = currency  # 當前設定的貨幣代碼
        self.his_data = None      # 用於存儲歷史匯率數據的 DataFrame
        self.currencies = None    # 可用貨幣代碼列表 (從網站獲取)
        self.check = None         # 布林值，表示 self.currency 是否為有效/可查詢的貨幣
        self.cur_dict = {}        # 字典，用於存儲貨幣代碼與其中文名稱的對應關係

    def _html(self, url):
        """
        私有輔助方法，用於發送 HTTP GET 請求並使用 BeautifulSoup 解析 HTML 內容。

        Args:
            url (str): 要抓取的網頁 URL。

        Returns:
            BeautifulSoup object or None: 解析後的 Soup 對象，若請求失敗則可能觸發異常。
        """
        # 發送 GET 請求，設定超時時間為10秒
        r = requests.get(url, timeout=10)
        # 設定正確的響應編碼 (網站使用 UTF-8)
        r.encoding = 'utf_8'
        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(r.text, "html.parser")
        return soup

    # 台灣銀行歷史營業時間黃金存摺牌價(2019年至今)
    def gold(self, show_plot=True): # 修改參數名稱以更清晰，並符合PEP8
        """
        下載台灣銀行黃金歷史數據並可選擇是否繪製價格走勢圖。
        數據會保存到 'data/GOLD_YYYYMMDD.pkl' 檔案中。

        Args:
            show_plot (bool): 是否顯示價格走勢圖，預設為 True。

        Returns:
            pandas.DataFrame: 包含黃金歷史價格數據的 DataFrame。
        """
        existing_gold_files = glob.glob(os.path.join('data', 'GOLD_*.pkl')) # 使用 os.path.join 並更名
        current_time = datetime.datetime.now()
        # 計算獲取數據的結束日期 (下個月的第一天)
        # 若當前月份為12月，則下個月為明年的1月
        if current_time.month == 12:
            end_date = datetime.date(current_time.year + 1, 1, 1)
        else:
            end_date = datetime.date(current_time.year, current_time.month + 1, 1)

        all_gold_data = pd.DataFrame() # 初始化為空的 DataFrame

        if existing_gold_files:
            # 如果存在現有數據檔案，讀取數據並設定開始日期為現有數據的最後月份
            print(f"找到現有黃金數據檔案: {existing_gold_files[0]}") # 提示信息
            all_gold_data = pd.read_pickle(existing_gold_files[0])
            latest_data_date = all_gold_data['日期'].max()
            # 設定開始日期為已下載數據的最後一個月份的第一天，以便從下個月開始更新
            if latest_data_date.month == 12:
                 start_date = datetime.date(latest_data_date.year + 1, 1, 1)
            else:
                 start_date = datetime.date(latest_data_date.year, latest_data_date.month + 1, 1)
            
            # 如果開始日期已經等於或超過結束日期，表示數據已是最新，無需下載
            if start_date >= end_date:
                print("黃金數據已是最新。") # 即使數據最新，仍會繼續執行後續的保存操作，確保檔案名日期更新
            
            # 移除舊檔案，因為之後會保存包含所有（包括更新的）數據的新檔案
            os.remove(existing_gold_files[0])
        else:
            # 如果沒有現有數據，則設定開始日期為結束日期的一年前
            print("未找到現有黃金數據檔案，將下載過去一年的數據。") # 提示信息
            start_date = datetime.date(end_date.year - 1, end_date.month, 1) # 從一年前的當月開始

        # 迭代獲取每個月的數據直到結束日期
        current_process_date = start_date
        # fetched_any_new_data = False # 此標記先前用於判斷是否保存，現已移除，無論如何都會嘗試保存
        last_monthly_columns = None # 用於保存最後一次成功獲取數據的欄位，以確保最終DataFrame的欄位順序一致

        while current_process_date < end_date: # 修改條件為 < (小於，因為 end_date 是下個月1號)
            print(f"正在獲取 {current_process_date.year} 年 {current_process_date.month:02d} 月黃金數據...") # 提供處理進度信息
            source_url = f'https://rate.bot.com.tw/gold/csv/{current_process_date.year}-{current_process_date.month:02d}/TWD/0'
            
            try:
                monthly_gold_data = pd.read_csv(source_url)
                if not monthly_gold_data.empty:
                    # 將 '日期' 列轉換為 datetime 對象
                    monthly_gold_data['日期'] = pd.to_datetime(
                        monthly_gold_data['日期'].astype('str'), format='%Y%m%d') # 修改為 str 再轉日期
                    
                    all_gold_data = pd.concat([all_gold_data, monthly_gold_data], axis=0, ignore_index=True, sort=False)
                    fetched_any_new_data = True
                    last_monthly_columns = monthly_gold_data.columns # 保存欄位信息
                else:
                    print(f'{current_process_date.year} 年 {current_process_date.month:02d} 月沒有數據。')
            except Exception as e:
                print(f"獲取 {current_process_date.year} 年 {current_process_date.month:02d} 月數據時發生錯誤: {e}")

            # 更新到下一個月份
            if current_process_date.month == 12:
                current_process_date = datetime.date(current_process_date.year + 1, 1, 1)
            else:
                current_process_date = datetime.date(current_process_date.year, current_process_date.month + 1, 1)

        if not all_gold_data.empty:
            # 數據清洗：去除重複項，按日期排序，重置索引
            # 確保 '日期' 欄位存在
            if '日期' in all_gold_data.columns:
                all_gold_data = all_gold_data.drop_duplicates(subset=['日期']).sort_values(
                    '日期').reset_index(drop=True)
                # 如果在迴圈中成功獲取過數據，使用那時的欄位順序
                if last_monthly_columns is not None:
                     all_gold_data = all_gold_data[last_monthly_columns]
            else:
                print("警告: '日期' 欄位不存在於合併後的黃金數據中。")

        # 保存處理後的數據到 .pkl 檔案
        output_file_path = os.path.join('data', f'GOLD_{current_time.strftime("%Y%m%d")}.pkl')
        try:
            all_gold_data.to_pickle(output_file_path)
            print(f"黃金數據已保存至: {output_file_path}")
        except Exception as e:
            print(f"保存黃金數據失敗: {e}")
        
        self.gold_data = all_gold_data # 將數據存儲到實例變數

        if show_plot and not all_gold_data.empty and '日期' in all_gold_data.columns and '本行買入價格' in all_gold_data.columns and '本行賣出價格' in all_gold_data.columns:
            # 如果需要，繪製黃金價格走勢圖
            plt.plot('日期', '本行買入價格', data=all_gold_data, label='銀行買入價 (您賣出)') # 更清晰的標籤
            plt.plot('日期', '本行賣出價格', data=all_gold_data, label='銀行賣出價 (您買入)') # 更清晰的標籤
            plt.legend()
            plt.title('台灣銀行黃金歷史價格走勢圖') # 更完整的標題
            plt.xlabel('日期') # X軸標籤
            plt.ylabel('價格 (新台幣)') # Y軸標籤
            plt.xticks(rotation=45)
            plt.grid(True) # 添加網格線
            plt.tight_layout() # 自動調整佈局
            plt.show()
        elif show_plot:
            print("沒有黃金數據可供繪圖，或數據欄位不完整。")

        return all_gold_data

    # 目前台灣銀行黃金牌價
    def gold_now(self):
        """
        從台灣銀行網站獲取並顯示目前的黃金牌價。
        資訊包含牌價更新時間、黃金品名、本行買入價格和本行賣出價格。
        此方法直接將結果打印到控制台。
        """
        url = 'https://rate.bot.com.tw/gold?Lang=zh-TW'
        try:
            # 使用既有的 _html 方法來獲取 soup 對象，以統一請求處理方式
            soup = self._html(url)

            # 提取牌價更新時間
            update_time_element = soup.find(class_="pull-left trailer text-info")
            if update_time_element:
                update_time = update_time_element.text.replace('\n', '').replace("\r", '').strip()
                print(f"{update_time}\n{'--' * 20}")
            else:
                print("無法獲取牌價更新時間。")
                print(f"{'--' * 20}")


            # 提取黃金品名 (例如 "黃金牌價")
            gold_product_name_element = soup.find("td", class_="rowSP_Ctrl_2_4_4 set-title-L-min-width-class")
            if gold_product_name_element:
                gold_product_name = gold_product_name_element.text.split("\r")[0].strip()
                print(gold_product_name)
            else:
                print("無法獲取黃金品名。")

            # 提取本行買入價格
            # "rowSP_Ctrl_0_2_2 highlight text-center set-title-R-min-width-class" 通常對應 "本行買入價格" 的標題
            # "text-right" class 的第一個元素通常是其對應的價格
            buy_price_label_element = soup.find("td", class_="rowSP_Ctrl_0_2_2 highlight text-center set-title-R-min-width-class")
            buy_price_value_element = soup.find_all("td", class_="text-right") # 價格通常在這個 class

            if buy_price_label_element and buy_price_value_element and len(buy_price_value_element) > 0:
                buy_price_label = buy_price_label_element.text.strip()
                buy_price_value = buy_price_value_element[0].text.strip()
                print(f'{buy_price_label}: {buy_price_value}')
            else:
                print("無法獲取本行買入價格。")

            # 提取本行賣出價格
            # "rowSP_Ctrl_0_2_2 highlight text-center" 通常對應 "本行賣出價格" 的標題
            # "text-right" class 的第二個元素通常是其對應的價格
            sell_price_label_element = soup.find("td", class_="rowSP_Ctrl_0_2_2 highlight text-center")
            # sell_price_value_element = soup.find_all("td", class_="text-right") # buy_price_value_element 已經獲取了所有 text-right

            if sell_price_label_element and buy_price_value_element and len(buy_price_value_element) > 1:
                sell_price_label = sell_price_label_element.text.strip()
                sell_price_value = buy_price_value_element[1].text.strip()
                print(f'{sell_price_label}: {sell_price_value}')
            else:
                print("無法獲取本行賣出價格。")

        except requests.exceptions.RequestException as e:
            print(f"獲取目前黃金牌價時發生網路錯誤: {e}")
        except AttributeError as e:
            print(f"解析目前黃金牌價HTML時發生錯誤，可能是網頁結構已更改: {e}")
        except Exception as e:
            print(f"獲取目前黃金牌價時發生未預期錯誤: {e}")


    def save_pkl(self, data, currency_name): # 修改參數名稱以更清晰
        """
        將 DataFrame 保存到 pickle 檔案。

        Args:
            data (pandas.DataFrame): 要保存的數據。
            currency_name (str): 貨幣名稱或標識，用於構成檔案名 (例如 GOLD 或 USD)。
        """
        # 使用 os.path.join 處理路徑
        current_time = datetime.datetime.now()
        file_path = os.path.join(
            'data',
            f'{currency_name}_{current_time.strftime("%Y%m%d")}.pkl'
        )
        try:
            data.to_pickle(file_path)
            print(f"數據已保存至: {file_path}")
        except Exception as e:
            print(f"保存數據至 {file_path} 失敗: {e}")


    # 抓取能用的幣別
    def check_cur(self):
        """
        從 findrate.tw 網站檢查當前設定的 self.currency 是否為可用的幣別。
        結果會設定 self.currencies (可用幣別列表) 和 self.check (布林值)。
        如果幣別不可用，會打印提示訊息。
        """
        url = "https://www.findrate.tw/currency.php"
        try:
            soup = self._html(url)
            currency_elements_container = soup.find_all(class_="listbtns center")
            if not currency_elements_container:
                print("無法在網頁上找到幣別列表容器。")
                self.currencies = []
                self.check = False
                return

            # currency_links = currency_elements_container[0].find('li') # 原碼是 .find('li') 但通常 ul/ol 下有多個 li
            # 假設 'li' 是父標籤，而連結在 'a' 標籤中
            currency_links = currency_elements_container[0].find_all('a', href=True)

            if not currency_links:
                print("無法在幣別列表容器中找到任何幣別連結。")
                self.currencies = []
                self.check = False
                return

            self.currencies = []
            for link_tag in currency_links:
                href_value = link_tag['href'] # 例如 /USD/ 或 /JPY/
                # 解析 href 以獲取幣別代碼，例如從 "/USD/" 提取 "USD"
                currency_code = href_value.strip('/').split('/')[0] 
                if currency_code: # 確保成功解析出幣別代碼
                     self.currencies.append(currency_code)
            
            self.check = self.currency in self.currencies # 檢查當前實例的幣別是否在獲取的列表中
            if not self.check:
                print(f"錯誤：指定的幣別 '{self.currency}' 在 findrate.tw 上不可用或未被識別。")
                print(f"可用的幣別代碼為: {self.currencies}")
        except requests.exceptions.RequestException as e:
            print(f"檢查可用幣別時發生網路錯誤: {e}")
            self.currencies = [] # 發生錯誤時，清空列表
            self.check = False
        except AttributeError as e:
            print(f"解析可用幣別HTML時發生錯誤，可能是網頁結構已更改: {e}")
            self.currencies = []
            self.check = False
        except Exception as e:
            print(f"檢查可用幣別時發生未預期錯誤: {e}")
            self.currencies = []
            self.check = False


    def _currencies(self, show_names=True): # 參數改名 show -> show_names
        """
        從 findrate.tw 獲取所有可用幣別的英文代碼和對應的中文名稱。
        並將結果存儲在 self.cur_dict 中。

        Args:
            show_names (bool): 是否返回幣別字典。預設為 True。

        Returns:
            dict or None: 如果 show_names 為 True，返回包含幣別代碼和中文名稱的字典，否則不返回。
        """
        url = "https://www.findrate.tw/currency.php"
        self.cur_dict = {} # 初始化為空字典
        try:
            soup = self._html(url)
            currency_elements_container = soup.find_all(class_="listbtns center")
            if not currency_elements_container:
                print("無法在網頁上找到幣別列表容器 (_currencies)。")
                return None if show_names else None

            # 假設 'li' 是父標籤，而連結和名稱在 'a' 標籤中
            currency_links = currency_elements_container[0].find_all('a', href=True)
            if not currency_links:
                print("無法在幣別列表容器中找到任何幣別連結 (_currencies)。")
                return None if show_names else None

            english_codes = []
            traditional_chinese_names = []

            for link_tag in currency_links:
                href_value = link_tag['href'] # 例如 /USD/
                # 解析 href 以獲取幣別代碼
                currency_code = href_value.strip('/').split('/')[0] # 例如 "USD"
                # 提取 `<a>` 標籤的文本內容作為幣別中文名稱
                currency_name = link_tag.text.strip() # 例如 "美金"
                
                if currency_code and currency_name: # 確保兩者都成功提取
                    english_codes.append(currency_code)
                    traditional_chinese_names.append(currency_name)
            
            # 將英文代碼和中文名稱配對存入字典
            if len(english_codes) == len(traditional_chinese_names):
                for i in range(len(english_codes)):
                    self.cur_dict[english_codes[i]] = traditional_chinese_names[i]
            else:
                print("警告: 獲取的幣別代碼和中文名稱數量不匹配。")


            if show_names:
                return self.cur_dict
        
        except requests.exceptions.RequestException as e:
            print(f"獲取幣別列表時發生網路錯誤: {e}")
            # self.cur_dict 保持為 {}
            return None if show_names else None
        except AttributeError as e:
            print(f"解析幣別列表HTML時發生錯誤，可能是網頁結構已更改: {e}")
            return None if show_names else None
        except Exception as e:
            print(f"獲取幣別列表時發生未預期錯誤: {e}")
            return None if show_names else None
        return None # 確保在所有情況下，如果 show_names 為 True 但發生問題，也返回 None

    def _onepage(self, year, page_number): # Renamed 'page' to 'page_number' for clarity
        """
        從 findrate.tw 網站抓取指定貨幣、年份和頁數的歷史匯率數據。

        Args:
            year (int): 要查詢的年份。
            page_number (int): 要查詢的頁數。

        Returns:
            pandas.DataFrame: 包含該頁匯率數據的 DataFrame。如果無法獲取或解析數據，則返回空的 DataFrame。
        """
        if not self.currencies: # 檢查 self.currencies 是否已初始化 (可能尚未調用 check_cur)
            self.check_cur()
        
        if not self.check: # 如果 self.check 依然是 False (例如幣別不支援)
            print(f"錯誤：幣別 {self.currency} 不可用，無法獲取 {year} 年第 {page_number} 頁的數據。")
            return pd.DataFrame() # 返回空的 DataFrame

        url = f"https://historical.findrate.tw/his.php?c={self.currency}&year={year}&page={page_number}"
        try:
            soup = self._html(url)
            html_table = soup.find('table') # 更具描述性的變數名

            if not html_table:
                # 這種情況通常表示該年/頁沒有數據，網站可能直接不顯示表格
                # print(f"在 {year} 年第 {page_number} 頁 (幣別: {self.currency}) 未找到數據表格。")
                return pd.DataFrame()

            # 提取表頭 (column headers)
            header_row = html_table.find('tr')
            if not header_row:
                print(f"警告：在 {year} 年第 {page_number} 頁 (幣別: {self.currency}) 的表格中未找到表頭。")
                return pd.DataFrame()
            
            column_names = [th.text.strip() for th in header_row.find_all('th')]
            if not column_names:
                print(f"警告：在 {year} 年第 {page_number} 頁 (幣別: {self.currency}) 的表格表頭中未能提取到任何欄位名稱。")
                return pd.DataFrame()
            # 標準化第一個欄位的名稱為 '日期'，以確保後續處理的一致性
            column_names[0] = '日期' 

            # 提取表格數據行
            table_rows_html = html_table.find_all('tr')[1:] # 跳過表頭行 (索引為0的是表頭)
            
            if not table_rows_html:
                # print(f"在 {year} 年第 {page_number} 頁 (幣別: {self.currency}) 的表格中未找到數據行 (除了表頭)。")
                return pd.DataFrame()

            data_rows = []
            for row_html in table_rows_html:
                cell_values = [td.text.replace('\n', '').replace('\xa0', '').replace(' ', '').strip() 
                               for td in row_html.find_all('td')]
                if any(cell_values): # 只添加有實際數據的行
                    data_rows.append(cell_values)
            
            if not data_rows:
                # print(f"在 {year} 年第 {page_number} 頁 (幣別: {self.currency}) 的表格中未提取到有效數據內容。")
                return pd.DataFrame()

            page_data_df = pd.DataFrame(data=data_rows, columns=column_names)
            
            # 將 '-' 替換為 NaN (Not a Number)，表示缺失數據
            page_data_df.replace('-', np.nan, inplace=True)
            
            return page_data_df

        except requests.exceptions.RequestException as e:
            print(f"獲取 {year} 年第 {page_number} 頁 ({self.currency}) 數據時發生網路錯誤: {e}")
            return pd.DataFrame()
        except AttributeError as e:
            print(f"解析 {year} 年第 {page_number} 頁 ({self.currency}) HTML時發生錯誤，可能是網頁結構已更改: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"獲取或解析 {year} 年第 {page_number} 頁 ({self.currency}) 數據時發生未預期錯誤: {e}")
            return pd.DataFrame()

    # 抓取今日所有匯率
    def now_all(self):
        """
        從 findrate.tw 網站抓取所有幣別目前的即時匯率資訊。
        數據包含幣別名稱、幣別代碼、即期買入/賣出、現鈔買入/賣出等。
        結果會存儲在 self.now_all_data 並返回。

        Returns:
            pandas.DataFrame: 包含所有幣別即時匯率的 DataFrame。
                              如果無法獲取或解析數據，則返回空的 DataFrame。
        """
        url = "https://www.findrate.tw/currency.php" # 與 _currencies 和 check_cur 使用相同URL
        print(f"正在從 {url} 抓取所有幣別的即時匯率...")
        try:
            soup = self._html(url)
            
            # 通常匯率表格在第一個<tbody>中
            # 網頁結構可能有多個<tbody>，需謹慎選擇
            # 在此網站，第一個 tbody 包含主要匯率表
            rate_table_body = soup.find('tbody') 
            if not rate_table_body:
                print(f"錯誤：在 {url} 未找到匯率表格的 tbody 元素。")
                self.now_all_data = pd.DataFrame()
                return self.now_all_data

            header_row_html = rate_table_body.find('tr') # 表頭行
            if not header_row_html:
                print(f"錯誤：在匯率表格中未找到表頭行。")
                self.now_all_data = pd.DataFrame()
                return self.now_all_data

            column_names = [th.text.strip() for th in header_row_html.find_all('th')]
            if not column_names:
                print(f"錯誤：未能從表頭行提取任何欄位名稱。")
                self.now_all_data = pd.DataFrame()
                return self.now_all_data

            data_rows_html = rate_table_body.find_all('tr')[1:] # 數據行 (跳過表頭)
            if not data_rows_html:
                print(f"警告：在匯率表格中未找到任何數據行 (除了表頭)。")
                self.now_all_data = pd.DataFrame()
                return self.now_all_data
                
            all_rates_data = []
            for row_html in data_rows_html:
                # 清理每個儲存格的文本：移除換行符、不斷行空格、普通空格，並去除首尾空白
                cell_values = [td.text.replace('\n', '').replace('\xa0', '').replace(' ', '').strip() 
                               for td in row_html.find_all('td')]
                if any(cell_values): # 確保行內至少有一個非空儲存格
                    all_rates_data.append(cell_values)
            
            if not all_rates_data:
                print(f"警告：未能從匯率表格中提取到任何有效的數據內容。")
                self.now_all_data = pd.DataFrame()
                return self.now_all_data

            self.now_all_data = pd.DataFrame(data=all_rates_data, columns=column_names)
            print(f"成功抓取 {len(self.now_all_data)} 筆即時匯率數據。")
            # 可以考慮將 '--' 或空字符串替換為 np.nan，如果後續需要數值計算
            # self.now_all_data.replace(['--', ''], np.nan, inplace=True)
            return self.now_all_data

        except requests.exceptions.RequestException as e:
            print(f"抓取所有即時匯率時發生網路錯誤: {e}")
            self.now_all_data = pd.DataFrame()
            return self.now_all_data
        except AttributeError as e:
            print(f"解析所有即時匯率HTML時發生錯誤，可能是網頁結構已更改: {e}")
            self.now_all_data = pd.DataFrame()
            return self.now_all_data
        except Exception as e:
            print(f"抓取或解析所有即時匯率時發生未預期錯誤: {e}")
            self.now_all_data = pd.DataFrame()
            return self.now_all_data

    # 抓取年度單一匯率
    def _year(self, year_to_fetch): # Renamed 'year' to 'year_to_fetch'
        """
        抓取指定貨幣在特定年份的所有歷史匯率數據。
        此方法會迭代調用 _onepage() 來獲取所有分頁的數據，然後合併它們。

        Args:
            year_to_fetch (int): 要查詢的年份 (必須大於2009)。

        Returns:
            pandas.DataFrame: 包含該年度所有匯率數據的 DataFrame。
                              如果年份不符合要求或無法獲取數據，則返回空的 DataFrame。
        """
        if not isinstance(year_to_fetch, int) or year_to_fetch <= 2009:
            # 數據源 findrate.tw 的歷史數據通常從2010年開始
            print(f"錯誤：年份 '{year_to_fetch}' 不符合要求。請提供一個大於2009的整數年份。")
            return pd.DataFrame()

        if not self.currencies:
            self.check_cur() # 確保 self.currencies 和 self.check 已被設定
        
        if not self.check:
            print(f"錯誤：幣別 {self.currency} 不可用，無法獲取 {year_to_fetch} 年的數據。")
            return pd.DataFrame()

        yearly_data_list = [] # 用於存儲從每一頁獲取的 DataFrame
        # findrate.tw 的歷史數據每頁約25-30條，一年約250個交易日，大概需要 9-10 頁
        # 迭代足夠多的頁數以確保抓取全年數據，如果某頁沒有數據，_onepage 會返回空 DataFrame
        max_pages_to_try = 15 # 設定一個合理的上限頁數嘗試
        print(f"開始獲取 {self.currency} 在 {year_to_fetch} 年的匯率數據...")

        for page_num in range(1, max_pages_to_try + 1):
            # print(f"正在獲取 {year_to_fetch} 年第 {page_num} 頁...") # 可選：更詳細的進度提示
            single_page_df = self._onepage(year_to_fetch, page_num)
            
            if single_page_df.empty:
                # 如果 _onepage 返回空的 DataFrame，通常表示後續已無數據
                # print(f"{year_to_fetch} 年第 {page_num} 頁沒有數據，停止抓取此年份後續頁面。")
                break 
            yearly_data_list.append(single_page_df)

        if not yearly_data_list:
            print(f"未能獲取到 {self.currency} 在 {year_to_fetch} 年的任何數據。")
            return pd.DataFrame()

        # 合併從所有頁面獲取的數據
        combined_yearly_data = pd.concat(yearly_data_list, axis=0, ignore_index=True, sort=False)

        if '日期' not in combined_yearly_data.columns:
            print(f"警告：合併後的 {year_to_fetch} 年數據中缺少 '日期' 欄位。")
            return combined_yearly_data # 或者返回空 DataFrame，取決於後續處理的嚴格性

        # 數據處理
        try:
            combined_yearly_data['日期'] = pd.to_datetime(combined_yearly_data['日期'])
            # 按日期排序並重置索引
            combined_yearly_data = combined_yearly_data.sort_values('日期').reset_index(drop=True)
            
            # 將日期以外的其他欄位轉換為 float 型別
            # 先獲取 '日期' 欄位之後的所有欄位名稱
            numeric_columns = [col for col in combined_yearly_data.columns if col != '日期']
            if numeric_columns: # 確保有其他欄位可轉換
                # 使用 .loc 來避免 SettingWithCopyWarning
                for col in numeric_columns:
                    combined_yearly_data.loc[:, col] = pd.to_numeric(combined_yearly_data[col], errors='coerce')
            
            print(f"成功獲取並處理完畢 {self.currency} 在 {year_to_fetch} 年的數據，共 {len(combined_yearly_data)} 筆。")
            return combined_yearly_data
        except Exception as e:
            print(f"處理 {year_to_fetch} 年數據時發生錯誤: {e}")
            return pd.DataFrame() # 發生錯誤時返回空 DataFrame

    # 目前所有銀行單一匯率
    def now(self):
        """
        抓取指定單一貨幣 (self.currency) 在各家銀行的目前即時匯率。
        數據包含銀行名稱、即期買入/賣出、現鈔買入/賣出等。
        結果會存儲在 self.now_data 並返回，按「即期賣出」價格升序排列。

        Returns:
            pandas.DataFrame: 包含該貨幣在各銀行即時匯率的 DataFrame。
                              如果無法獲取或解析數據，或幣別不可用，則返回空的 DataFrame。
        """
        if not self.currencies: # 確保 self.currencies 和 self.check 已被設定
            self.check_cur()
        
        if not self.check:
            print(f"錯誤：幣別 {self.currency} 不可用，無法獲取其在各銀行的即時匯率。")
            self.now_data = pd.DataFrame()
            return self.now_data

        url = f"https://www.findrate.tw/{self.currency}/"
        print(f"正在從 {url} 抓取 {self.currency} 在各銀行的即時匯率...")
        try:
            soup = self._html(url)
            
            # 在此頁面 (findrate.tw/{currency}/)，各家銀行匯率表格通常是頁面中的第二個 <tbody>
            # 第一個 <tbody> 可能是其他全站共通的幣別列表或類似內容
            all_tbodies = soup.find_all('tbody')
            if len(all_tbodies) < 2: # 檢查是否有足夠的 tbody 元素
                print(f"錯誤：在 {url} 未找到足夠的 tbody 元素來定位銀行匯率表格。預期至少有兩個 tbody。")
                self.now_data = pd.DataFrame()
                return self.now_data
            
            target_tbody = all_tbodies[1] # 選擇第二個 tbody

            header_row_html = target_tbody.find('tr') # 表格的表頭行
            if not header_row_html:
                print(f"錯誤：在銀行匯率表格中未找到表頭行。")
                self.now_data = pd.DataFrame()
                return self.now_data
                
            column_names = [th.text.strip() for th in header_row_html.find_all('th')]
            if not column_names:
                print(f"錯誤：未能從銀行匯率表頭行提取任何欄位名稱。")
                self.now_data = pd.DataFrame()
                return self.now_data

            data_rows_html = target_tbody.find_all('tr')[1:]
            if not data_rows_html:
                print(f"警告：在銀行匯率表格中未找到任何數據行 (除了表頭)。")
                self.now_data = pd.DataFrame()
                return self.now_data

            bank_rates_list = []
            for row_html in data_rows_html:
                cell_values = [td.text.replace('\n', '').replace('\xa0', '').replace(' ', '').strip()
                               for td in row_html.find_all('td')]
                if any(cell_values):
                    bank_rates_list.append(cell_values)
            
            if not bank_rates_list:
                print(f"警告：未能從銀行匯率表格中提取到任何有效的數據內容 ({self.currency})。")
                self.now_data = pd.DataFrame()
                return self.now_data

            self.now_data = pd.DataFrame(data=bank_rates_list, columns=column_names)
            
            # 將 '--' 替換為 NaN 以便進行數值比較和排序
            self.now_data.replace('--', np.nan, inplace=True)
            
            # 嘗試將匯率列轉換為數值型別，以便正確排序
            rate_columns_to_convert = ['即期買入', '即期賣出', '現鈔買入', '現鈔賣出']
            for col in rate_columns_to_convert:
                if col in self.now_data.columns:
                    self.now_data[col] = pd.to_numeric(self.now_data[col], errors='coerce')

            if '即期賣出' in self.now_data.columns:
                self.now_data = self.now_data.sort_values("即期賣出", ascending=True)
                print(f"成功抓取並排序 {len(self.now_data)} 家銀行的 {self.currency} 即時匯率數據。")
            else:
                print(f"警告：抓取的 {self.currency} 銀行匯率數據中缺少 '即期賣出' 欄位，無法排序。")

            return self.now_data

        except requests.exceptions.RequestException as e:
            print(f"抓取 {self.currency} 即時銀行匯率時發生網路錯誤: {e}")
            self.now_data = pd.DataFrame()
            return self.now_data
        except IndexError: # soup.find_all('tbody')[1] 可能引發
            print(f"解析 {self.currency} 即時銀行匯率HTML時發生索引錯誤，可能是網頁結構不符合預期 (tbody 數量不足)。")
            self.now_data = pd.DataFrame()
            return self.now_data
        except AttributeError as e:
            print(f"解析 {self.currency} 即時銀行匯率HTML時發生屬性錯誤，可能是網頁結構已更改: {e}")
            self.now_data = pd.DataFrame()
            return self.now_data
        except Exception as e:
            print(f"抓取或解析 {self.currency} 即時銀行匯率時發生未預期錯誤: {e}")
            self.now_data = pd.DataFrame()
            return self.now_data

    # 抓取近期單一匯率新聞
    def news(self):
        """
        抓取指定單一貨幣 (self.currency) 在 findrate.tw 上的近期相關新聞。
        新聞包含日期、標題和部分內容。
        結果會存儲在 self.news_data 並返回前10條新聞。

        Returns:
            pandas.DataFrame: 包含該貨幣近期新聞的 DataFrame (最多10條)。
                              如果無法獲取或解析數據，或幣別不可用，則返回空的 DataFrame。
        """
        if not self.currencies: # 確保 self.currencies 和 self.check 已被設定
            self.check_cur()
        
        if not self.check:
            print(f"錯誤：幣別 {self.currency} 不可用，無法獲取其相關新聞。")
            self.news_data = pd.DataFrame()
            return self.news_data

        url = f"https://www.findrate.tw/{self.currency}/"
        print(f"正在從 {url} 抓取 {self.currency} 的近期新聞...")
        try:
            soup = self._html(url)
            
            # 新聞通常在 class='newslist' 的元素中
            news_list_container = soup.find(class_='newslist') # 假設只有一個 newslist
            if not news_list_container:
                news_list_containers = soup.find_all(class_='newslist') # 嘗試 find_all
                if not news_list_containers:
                    print(f"錯誤：在 {url} 未找到新聞列表容器 (class='newslist')。")
                    self.news_data = pd.DataFrame()
                    return self.news_data
                news_list_container = news_list_containers[0] # 取第一個

            news_dates = [date_span.text.strip() for date_span in news_list_container.find_all("span")]
            news_titles = [title_h4.text.strip() for title_h4 in news_list_container.find_all("h4")]
            news_contexts = [context_p.text.strip() for context_p in news_list_container.find_all("p")]

            if not (news_dates and news_titles and news_contexts and 
                    len(news_dates) == len(news_titles) == len(news_contexts)):
                print(f"警告：未能完整提取新聞的日期、標題或內容，或者數量不匹配 ({self.currency})。")
                # 即使部分提取，也嘗試創建 DataFrame
                min_len = min(len(news_dates), len(news_titles), len(news_contexts))
                if min_len == 0 and not (news_dates or news_titles or news_contexts) : # 如果什麼都沒抓到
                     print(f"未提取到任何新聞內容 ({self.currency})。")
                     self.news_data = pd.DataFrame()
                     return self.news_data

                self.news_data = pd.DataFrame({
                    'date': news_dates[:min_len],
                    'title': news_titles[:min_len],
                    'context': news_contexts[:min_len]
                })
            else:
                self.news_data = pd.DataFrame({
                    'date': news_dates,
                    'title': news_titles,
                    'context': news_contexts
                })
            
            print(f"成功抓取 {len(self.news_data)} 條 {self.currency} 相關新聞。")
            return self.news_data.iloc[:10, :] # 按原樣返回前10條

        except requests.exceptions.RequestException as e:
            print(f"抓取 {self.currency} 新聞時發生網路錯誤: {e}")
            self.news_data = pd.DataFrame()
            return self.news_data
        except AttributeError as e:
            print(f"解析 {self.currency} 新聞HTML時發生錯誤，可能是網頁結構已更改: {e}")
            self.news_data = pd.DataFrame()
            return self.news_data
        except Exception as e:
            print(f"抓取或解析 {self.currency} 新聞時發生未預期錯誤: {e}")
            self.news_data = pd.DataFrame()
            return self.news_data


    # 抓取近十年單一匯率資料(2010年至今)
    def history(self):
        """
        抓取指定貨幣自2010年至今的歷史匯率數據。
        此方法會先檢查本地是否有已保存的數據，並根據情況決定是全新抓取還是更新現有數據。
        最終數據會保存在 self.his_data 並存檔為 .pkl 檔案。

        Returns:
            pandas.DataFrame: 包含該貨幣歷史匯率數據的 DataFrame。
                              如果無法獲取或處理數據，則可能返回不完整或空的 DataFrame。
        """
        if not self.currencies: # 確保 self.currencies 和 self.check 已被設定
            self.check_cur()
        
        if not self.check:
            print(f"錯誤：幣別 {self.currency} 不可用，無法獲取歷史數據。")
            self.his_data = pd.DataFrame() # 確保設定為空 DataFrame
            return self.his_data

        current_time = datetime.datetime.now()
        current_year = current_time.year
        # 數據抓取的結束年份應為當前年份。_year 方法會抓取指定年份的全年數據。
        end_fetch_year = current_year 
        
        # 檔案名格式: CURRENCY_YYYYMMDD.pkl. 我們需要最新的那個檔案。
        existing_data_files = sorted(glob.glob(os.path.join('data', f'{self.currency}_*.pkl')), reverse=True)
        
        default_start_year = 2010 # 數據源通常從2010年開始
        start_fetch_year = default_start_year
        loaded_historical_data = pd.DataFrame() # 用於存儲從檔案載入的數據

        if existing_data_files:
            latest_file_path = existing_data_files[0]
            print(f"找到現有數據檔案: {latest_file_path}")
            try:
                loaded_historical_data = pd.read_pickle(latest_file_path)
                if not loaded_historical_data.empty and '日期' in loaded_historical_data.columns:
                    loaded_historical_data['日期'] = pd.to_datetime(loaded_historical_data['日期'])
                    
                    last_data_year_in_file = loaded_historical_data['日期'].max().year
                    
                    # 決定從哪個年份開始更新數據
                    # 如果檔案中的最新年份小於當前年份，從檔案最新年份的下一年開始抓取 (避免重複抓取已完整年份)
                    # 但如果檔案最新年份本身就比 default_start_year 還早(不太可能，但以防萬一)，則仍從 default_start_year 開始
                    if last_data_year_in_file < current_year:
                        start_fetch_year = max(default_start_year, last_data_year_in_file + 1)
                        print(f"現有數據截至 {last_data_year_in_file} 年，將從 {start_fetch_year} 年開始更新至 {current_year} 年。")
                        # 保留比 start_fetch_year 更早的數據
                        loaded_historical_data = loaded_historical_data[loaded_historical_data['日期'].dt.year < start_fetch_year]
                    else: # last_data_year_in_file == current_year
                        # 如果檔案數據已包含當前年份，則重新抓取當前年份以獲取最新數據
                        print(f"現有數據包含 {current_year} 年，將重新獲取 {current_year} 年數據以確保最新。")
                        start_fetch_year = current_year
                        # 清理掉當前年份的數據，準備用新的替換
                        loaded_historical_data = loaded_historical_data[loaded_historical_data['日期'].dt.year < current_year]
                    
                    # 移除所有此貨幣的舊檔案，因為之後會保存包含所有（包括更新的）數據的新檔案
                    for f_path in existing_data_files:
                        if f_path.startswith(os.path.join('data', f'{self.currency}_')):
                            try:
                                os.remove(f_path)
                                print(f"已刪除舊數據檔案: {f_path}")
                            except OSError as e:
                                print(f"刪除檔案 {f_path} 失敗: {e}")
                else:
                    print(f"警告：現有數據檔案 {latest_file_path} 為空或缺少 '日期' 欄位，將重新抓取所有數據。")
                    loaded_historical_data = pd.DataFrame() # 重置
            except Exception as e:
                print(f"讀取或處理現有數據檔案 {latest_file_path} 時發生錯誤: {e}。將重新抓取所有數據。")
                loaded_historical_data = pd.DataFrame() # 重置
        else:
            print(f"未找到 {self.currency} 的現有數據檔案，將從 {start_fetch_year} 年開始全新抓取。")

        # 迭代抓取每一年的數據
        newly_fetched_data_list = []

        # 如果 start_fetch_year > end_fetch_year (例如，本地數據已是最新到當年，且當年數據被認為是最新的)
        # 則此迴圈不執行
        current_processing_year = start_fetch_year
        while current_processing_year <= end_fetch_year:
            print(f"正在獲取 {self.currency} 在 {current_processing_year} 年的匯率數據...")
            yearly_data = self._year(current_processing_year) # _year 已經包含了錯誤處理和打印信息
            if not yearly_data.empty:
                newly_fetched_data_list.append(yearly_data)
            current_processing_year += 1
        
        # 合併數據：首先是已載入的舊數據（如果有的話），然後是新抓取的數據
        final_data_list = []
        if not loaded_historical_data.empty:
            final_data_list.append(loaded_historical_data)
        if newly_fetched_data_list:
            final_data_list.extend(newly_fetched_data_list)

        if not final_data_list:
            print(f"未能獲取到任何 {self.currency} 的歷史數據。")
            self.his_data = pd.DataFrame()
            return self.his_data

        self.his_data = pd.concat(final_data_list, axis=0, ignore_index=True, sort=False)
        
        if '日期' in self.his_data.columns and not self.his_data.empty:
            self.his_data['日期'] = pd.to_datetime(self.his_data['日期']) # 確保日期欄位為 datetime 物件
            # 數據清洗：移除基於 '日期' 的重複記錄，保留最後一筆 (通常是最新或最完整的)，然後按日期排序並重置索引
            self.his_data = self.his_data.drop_duplicates(subset=['日期'], keep='last').sort_values('日期').reset_index(drop=True)
            print(f"數據合併與清洗完成，總計 {len(self.his_data)} 筆 {self.currency} 數據。")
        elif self.his_data.empty:
             print(f"沒有歷史數據可供處理 ({self.currency})。") # 例如，如果所有年份都沒有數據
        else:
            print(f"警告：合併後的歷史數據中缺少 '日期' 欄位 ({self.currency})。")
            
        if not self.his_data.empty:
            self.save_pkl(self.his_data, self.currency)
        else:
            print(f"沒有數據可保存 ({self.currency})。")
            
        return self.his_data

    def suggest_buying_rate(self, currency_data, window_size=20, std_multiplier=1.5):
        """
        根據歷史匯率數據，使用移動平均和標準差模型來建議潛在的買入時機。

        Args:
            currency_data (pd.DataFrame): 包含歷史匯率數據的 DataFrame。
                                          預期至少包含 '日期' 和 '即期賣出' (銀行賣出價) 欄位。
            window_size (int): 用於計算移動平均和標準差的天數窗口大小。預設為 20 天。
            std_multiplier (float): 標準差的乘數，用於設定買入閾值。預設為 1.5。

        Returns:
            pandas.DataFrame or None: 包含原始數據以及計算出的移動平均、標準差、
                                     買入建議閾值和買入訊號的 DataFrame。
                                     如果輸入驗證失敗或發生錯誤，則返回 None。
        """
        # --- 1. 輸入驗證 ---
        if not isinstance(currency_data, pd.DataFrame) or currency_data.empty:
            print("錯誤：提供的 'currency_data' 不是有效的 pandas DataFrame 或為空。")
            return None

        required_columns = ['日期', '即期賣出']
        for col in required_columns:
            if col not in currency_data.columns:
                print(f"錯誤：'currency_data' 中缺少必要的欄位 '{col}'。")
                return None

        if not isinstance(window_size, int) or window_size <= 0:
            print("錯誤：'window_size' 必須是正整數。")
            return None
        
        if len(currency_data) < window_size:
            print(f"錯誤：數據量 ({len(currency_data)} 筆) 不足，無法以 {window_size} 天作為窗口大小進行計算。")
            return None

        if not isinstance(std_multiplier, (float, int)) or std_multiplier <= 0:
            print("錯誤：'std_multiplier' 必須是正數。")
            return None

        # --- 2. 數據準備 ---
        # 複製一份數據以避免修改原始 DataFrame
        data = currency_data.copy()

        # 確保 '日期' 欄位是 datetime 型別並排序
        try:
            data['日期'] = pd.to_datetime(data['日期'])
        except Exception as e:
            print(f"錯誤：轉換 '日期' 欄位為 datetime 型別時發生錯誤: {e}")
            return None
        data = data.sort_values(by='日期').reset_index(drop=True)

        # 確保 '即期賣出' 欄位是數值型別
        if not pd.api.types.is_numeric_dtype(data['即期賣出']):
            print("提示：'即期賣出' 欄位不是數值型別，嘗試轉換...")
            data['即期賣出'] = pd.to_numeric(data['即期賣出'], errors='coerce')
            if data['即期賣出'].isnull().any():
                print("警告：'即期賣出' 欄位在轉換為數值型別後存在 NaN 值，可能影響計算結果。")
        
        # 再次檢查轉換後是否存在NaN，如果關鍵的 '即期賣出' 列大量為NaN，則模型無意義
        if data['即期賣出'].isnull().all():
            print("錯誤：'即期賣出' 欄位所有值均為 NaN，無法進行計算。")
            return None

        # --- 3. 計算指標 ---
        # 計算 N 日移動平均 (MA)
        data['移動平均'] = data['即期賣出'].rolling(window=window_size, min_periods=1).mean()
        
        # 計算 N 日標準差 (SD)
        data['標準差'] = data['即期賣出'].rolling(window=window_size, min_periods=1).std()
        
        # 計算買入建議閾值: MA - (std_multiplier * SD)
        data['買入建議閾值'] = data['移動平均'] - (std_multiplier * data['標準差'])
        
        # --- 4. 生成買入訊號 ---
        # 當 '即期賣出' 價格低於 '買入建議閾值' 時，視為一個潛在買入訊號
        # 為了避免在 NaN 值上比較，我們可以使用 .fillna(False) 處理比較結果中的 NaN
        # data['買入訊號'] = (data['即期賣出'] < data['買入建議閾值']).astype(int)
        
        # 更精確的訊號：前一天不滿足，當天滿足
        # 為了簡化，這裡使用簡單的閾值交叉判斷
        # Shift '即期賣出' and '買入建議閾值' to compare current day with previous day's state for signal generation
        # prev_spot_sell = data['即期賣出'].shift(1) # 前一日的即期賣出價
        # prev_threshold = data['買入建議閾值'].shift(1) # 前一日的買入建議閾值
        
        # 生成買入訊號的條件：
        # 1. 當前 '即期賣出' 價格低於當前 '買入建議閾值'
        # (可選進階條件，避免連續訊號：且前一日的 '即期賣出' 價格高於或等於前一日的 '買入建議閾值')
        # 為保持模型簡單，此處僅使用基本條件：目前價格 < 建議閾值
        
        conditions = [
            (data['即期賣出'] < data['買入建議閾值']) # 條件：即期賣出價小於買入建議閾值
        ]
        choices = [1] # 若條件成立，買入訊號為 1 (買入)
        data['買入訊號'] = np.select(conditions, choices, default=0) # 否則為 0 (不買入/持有)
        
        # 處理因滾動窗口計算導致在數據開頭部分產生的 NaN 值：
        # 如果 '移動平均' 是 NaN (通常在數據序列的開頭，因為窗口未滿)，
        # 則 '買入建議閾值' 和 '買入訊號' 也應該是 NaN，表示無法提供有效建議或訊號。
        # data.loc[data['移動平均'].isnull(), '買入訊號'] = 0 # 原先考慮設為0，但設為NaN更準確反映數據不足

        # --- 5. 返回結果 ---
        # 選擇最終要返回的欄位
        result_df = data[['日期', '即期賣出', '移動平均', '標準差', '買入建議閾值', '買入訊號']].copy()
        
        # 確保在窗口期內的 NaN 值在 '買入建議閾值' 和 '買入訊號' 中也得到合理處理
        # 若 '移動平均' 為 NaN，則相關的建議和訊號也應為 NaN
        result_df.loc[result_df['移動平均'].isnull(), ['買入建議閾值', '買入訊號']] = np.nan

        print(f"已成功生成買入建議數據，共 {len(result_df)} 筆。")
        return result_df

    # 單一匯率歷史趨勢圖 (指定起始年)
    def plot(self, target_year=2010, show_suggestions=False, window_size=20, std_multiplier=1.5):
        """
        繪製指定貨幣從某年份開始的歷史匯率走勢圖。
        可選擇是否同時顯示基於移動平均和標準差的買入建議閾值。

        Args:
            target_year (int): 起始年份，預設為 2010。
            show_suggestions (bool): 是否顯示買入建議閾值。預設為 False。
            window_size (int): 用於計算建議模型的移動平均窗口大小。預設為 20。
            std_multiplier (float): 用於計算建議模型的標準差乘數。預設為 1.5。
        """
        # 檢查是否有歷史數據，若無則嘗試獲取
        if self.his_data is None:
            print(f"提示：尚未獲取 {self.currency} 的歷史數據，現在開始獲取...")
            if not self.currencies: # 確保幣別列表已加載
                self.check_cur()
            
            if self.check: # 如果幣別有效
                self.history() # 調用 history 方法獲取數據
            else:
                print(f"錯誤：無法獲取 {self.currency} 的歷史數據，因幣別名稱 '{self.currency}' 不正確或不可用。")
                return # 結束方法

        # 再次檢查歷史數據是否成功獲取
        if self.his_data is None or self.his_data.empty:
            print(f"錯誤：沒有可供繪圖的 {self.currency} 歷史數據。")
            return

        # 獲取幣別中文名稱，用於圖表標題
        if not self.cur_dict: # 確保 self.cur_dict 已被設定
             self._currencies(show_names=False) 
        currency_chinese_name = self.cur_dict.get(self.currency, self.currency)

        # 檢查繪圖所需的基本欄位是否存在
        required_plot_columns = ['日期', '即期買入', '即期賣出']
        missing_cols = [col for col in required_plot_columns if col not in self.his_data.columns or pd.isnull(self.his_data[col]).all()]
        if missing_cols:
            print(f"錯誤：{currency_chinese_name} 歷史數據中缺少或全部為空的必要欄位: {missing_cols}。無法繪製匯率圖。")
            return

        # 根據 target_year 篩選要繪製的歷史數據
        # 確保 self.his_data['日期'] 是 datetime 物件
        if not pd.api.types.is_datetime64_any_dtype(self.his_data['日期']):
             self.his_data['日期'] = pd.to_datetime(self.his_data['日期'], errors='coerce')
        
        # 過濾掉日期轉換失敗的行
        self.his_data.dropna(subset=['日期'], inplace=True)

        target_display_df = self.his_data[self.his_data['日期'] >= pd.Timestamp(f'{target_year}-01-01')].copy()

        if target_display_df.empty:
            print(f"提示：在 {target_year} 年之後沒有 {currency_chinese_name} 的歷史數據可供繪圖。")
            return

        # ---- 開始繪圖 ----
        plt.figure(figsize=(15, 7)) # 設定圖表大小

        # 繪製即期買入和即期賣出價格
        plt.plot('日期', '即期買入', data=target_display_df, label='即期買入 (銀行賣出)', color='orangered')
        plt.plot('日期', '即期賣出', data=target_display_df, label='即期賣出 (銀行買入)', color='dodgerblue')

        plot_title_suffix = "" # 圖表標題的後綴

        # 如果要求顯示買入建議
        if show_suggestions:
            print(f"提示：正在為 {self.currency} 計算買入建議數據...")
            # 使用完整的 self.his_data 計算建議，以獲得更準確的移動平均等指標
            suggestions_df = self.suggest_buying_rate(
                currency_data=self.his_data.copy(), # 傳遞副本以防萬一
                window_size=window_size,
                std_multiplier=std_multiplier
            )
            
            if suggestions_df is not None and not suggestions_df.empty and '買入建議閾值' in suggestions_df.columns:
                # 篩選建議數據以匹配 target_display_df 的日期範圍
                # 確保 suggestions_df['日期'] 也是 datetime 物件
                if not pd.api.types.is_datetime64_any_dtype(suggestions_df['日期']):
                    suggestions_df['日期'] = pd.to_datetime(suggestions_df['日期'], errors='coerce')
                
                suggestions_to_plot = suggestions_df[suggestions_df['日期'] >= pd.Timestamp(f'{target_year}-01-01')].copy()
                
                if not suggestions_to_plot.empty:
                    plt.plot('日期', '買入建議閾值', data=suggestions_to_plot, label='買入建議閾值', color='green', linestyle='--')
                    plot_title_suffix = " (含買入建議)" # 更新標題後綴
                    print(f"提示：已添加買入建議閾值到圖表。")
                else:
                    print(f"警告：計算出的買入建議數據在 {target_year} 年之後無有效值可繪製。")
            else:
                print(f"警告：未能生成 {self.currency} 的買入建議數據，或返回的數據不符合預期。")
        
        plt.legend() # 顯示圖例
            
        # 計算統計數據用於標題
        min_sell_price = target_display_df["即期賣出"].min()
        max_buy_price = target_display_df["即期買入"].max()
        
        return_info = '報酬率無法計算'
        if pd.notnull(min_sell_price) and pd.notnull(max_buy_price) and min_sell_price != 0:
            max_return_rate = round(max_buy_price / min_sell_price, 3)
            return_info = f'期間最高潛在報酬率: {max_return_rate}'
        
        title = (f'{currency_chinese_name} ({self.currency}) 匯率走勢圖 ({target_year}年至今){plot_title_suffix}\n'
                 f'最低銀行買入價(您賣出): {min_sell_price:.4f}, 最高銀行賣出價(您買入): {max_buy_price:.4f}\n'
                 f'{return_info}')
        plt.title(title, fontsize=14)
        plt.xlabel('日期', fontsize=12) 
        plt.ylabel('匯率 (新台幣)', fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.tight_layout() # 自動調整佈局
        plt.show()


if __name__ == '__main__':
    currency_list = NTex()._currencies()
    NTex().now_all()

    gold = NTex()
    gold.gold()
    gold.gold_now()
