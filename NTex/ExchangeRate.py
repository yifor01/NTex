import requests,datetime,glob,os
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from tqdm import tqdm
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

if not os.path.exists('data'):
    os.makedirs('data')

class NTex(object):
    def __init__(self,currency="USD"):
        self.currency = currency
        self.his_data = None
        self.currencies = None
        self.check = None

    def _html(self,url):
        r = requests.get(url)
        r.encoding = 'utf_8'
        soup = BeautifulSoup(r.text, "html.parser")
        return soup

    def save_pkl(self,data):
        data.to_pickle(f'data/{self.currency}_{datetime.datetime.now().strftime("%Y%m%d")}.pkl')

    # 抓取能用的幣別
    def check_cur(self):
        soup = self._html("https://www.findrate.tw/currency.php")
        self.currencies = [x.split('href="/')[1].split('/')[0] for x in str(soup.find_all(class_="listbtns center")[0].find('li')).split('\n')[:-1]]
        self.check = self.currency in self.currencies
        if not self.check:
            print('Unavilable currency')

    def _currencies(self):
        soup = self._html("https://www.findrate.tw/currency.php")
        currencies = pd.DataFrame({'zh':soup.find_all(class_="listbtns center")[0].find('li').text.split('\n')[:-1],
                                   'en':[x.split('href="/')[1].split('/')[0] for x in str(soup.find_all(class_="listbtns center")[0].find('li')).split('\n')[:-1]]})
        return currencies

    def _onepage(self,year,page):
        if not self.currencies:
            self.check_cur()
        if self.check:
            soup = self._html(f"https://historical.findrate.tw/his.php?c={self.currency}&year={year}&page={page}" )
            table = soup.find('table')
            columns = [th.text.replace('\n', '') for th in table.find('tr').find_all('th')]
            columns[0] = '日期'
            trs = table.find_all('tr')[1:]
            rows = list()
            for tr in trs:
                rows.append([td.text.replace('\n', '').replace('\xa0', '').replace(' ','') for td in tr.find_all('td')])
            onepage_data = pd.DataFrame(data=rows, columns=columns)
            onepage_data[onepage_data=='-'] = np.nan
            return onepage_data            

    # 抓取今日所有匯率
    def now_all(self):
        soup = self._html(f"https://www.findrate.tw/currency.php")
        table = soup.find_all('tbody')[0]
        columns = [th.text.replace('\n', '') for th in table.find('tr').find_all('th')]
        trs = table.find_all('tr')[1:]
        rows = list()
        for tr in trs:
            rows.append([td.text.replace('\n', '').replace('\xa0', '').replace(' ','') for td in tr.find_all('td')])
        self.now_all_data = pd.DataFrame(data=rows, columns=columns)
        return self.now_all_data

    # 抓取年度單一匯率
    def _year(self,year):
        assert year>2009
        if not self.currencies:
            self.check_cur()
        if self.check:
            web_data = pd.DataFrame({'A' : []})
            for page in range(1,10):
                page_data = self._onepage(year,page)
                web_data = pd.concat([web_data,page_data],axis=0)
            web_data['日期'] = pd.to_datetime(web_data['日期'])
            web_data = web_data.sort_values('日期').reset_index()[page_data.columns]
            web_data.iloc[:,1:] = web_data.iloc[:,1:].astype('float')
            return web_data
    
    # 目前所有銀行單一匯率
    def now(self):
        soup = self._html(f"https://www.findrate.tw/{self.currency}/")
        table = soup.find_all('tbody')[1]
        columns = [th.text.replace('\n', '') for th in table.find('tr').find_all('th')]
        if columns:
            trs = table.find_all('tr')[1:]
            rows = list()
            for tr in trs:
                rows.append([td.text.replace('\n', '').replace('\xa0', '').replace(' ','') for td in tr.find_all('td')])
            self.now_data = pd.DataFrame(data=rows, columns=columns)
            self.now_data[self.now_data=='--'] = np.nan
            return self.now_data
        else:
            print('no data')

    # 抓取近期單一匯率新聞
    def news(self):
        soup = self._html(f"https://www.findrate.tw/{self.currency}/")
        newslist = soup.find_all(class_ = 'newslist')[0]
        self.news_data = pd.DataFrame({'date':[td.text for td in newslist.find_all("span")],
                                       'title':[td.text for td in newslist.find_all("h4")],
                                       'context':[td.text for td in newslist.find_all("p")]})
        return self.news_data.iloc[:10,:]

    # 抓取近十年單一匯率資料(2010-now)
    def history(self): 
        if not self.currencies:
            self.check_cur()
        if self.check:
            for file in glob.glob(f'data\\{self.currency}_*.pkl'):
                if file!=f'data\\{self.currency}_{datetime.datetime.now().strftime("%Y%m%d")}.pkl':
                    os.remove(file)
                else:
                    self.his_data = pd.read_pickle(f'data/{self.currency}_{datetime.datetime.now().strftime("%Y%m%d")}.pkl')
            if self.his_data is None:
                self.his_data = self._year(2010)
                for year in tqdm(range(2011,datetime.datetime.now().year+1)):
                    tmp_data = self._year(year)
                    self.his_data = pd.concat([self.his_data,tmp_data],axis=0)
                self.his_data = self.his_data.reset_index().drop(columns='index')
                self.his_data['year'] = self.his_data['日期'].apply(lambda x:x.year)
                self.his_data['month'] = self.his_data['日期'].apply(lambda x:x.month)
                self.his_data['day'] = self.his_data['日期'].apply(lambda x:x.day)
                self.his_data['weekday'] = self.his_data['日期'].apply(lambda x:x.weekday()+1)
                self.save_pkl(self.his_data)
            return self.his_data.iloc[:,:5]
    
    # 單一匯率歷史趨勢圖 (指定起始年)
    def plot(self,target_year=2010):
        if self.his_data is None:
            print("Get Data First ...")
            if not self.currencies:
                self.check_cur()
            if self.check:
                self.history()
        target_df = self.his_data[self.his_data.year>=target_year]
        plt.plot('日期','即期買入',data=target_df,label='即期買入')
        plt.plot('日期','即期賣出',data=target_df,label='即期賣出')
        plt.legend()
        plt.title(f'{self.currency}匯率--最低買價:{target_df["即期賣出"].min()},最高賣價:{target_df["即期買入"].max()},最高報酬率:{round(target_df["即期買入"].max()/target_df["即期賣出"].min(),3)}')
        plt.xticks(rotation=45)
        plt.show()