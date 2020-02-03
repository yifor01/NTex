from ExchangeRate import NTex

NTex().currencies()
NTex().now_all()


USD = NTex(currency='USD')
USD.now()
USD.news()
USD.history()
USD.plot(2010)
USD._year(2020)