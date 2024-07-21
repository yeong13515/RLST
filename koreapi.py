import yaml
import json
import requests
import datetime
import os

class api: #api 클래스

    def __init__(self, config_path='ignore/config.yaml', token_path='ignore/token.dat', log_path = 'log/api'):
        self.load_config(config_path)
        self.token_path = token_path
        self.access_token = ""
        self.token_expiration = None
        self.load_token()
        self.log_path = log_path

    def load_config(self, path):
        with open(path, encoding='UTF-8') as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
        self.webhook_url = cfg['DISCORD_WEBHOOK_URL']
        self.app_key = cfg['APP_KEY']
        self.app_secret = cfg['APP_SECRET']
        self.url_base = cfg['URL_BASE']
        self.cano = cfg['CANO']
        self.acnt_prdt_cd = cfg['ACNT_PRDT_CD']

    def load_token(self):
        if os.path.exists(self.token_path):
            with open(self.token_path, 'r') as f:
                token_data = json.load(f)
                self.access_token = token_data['access_token']
                self.token_expiration = datetime.datetime.fromisoformat(token_data['time'])
                if datetime.datetime.now() < self.token_expiration:
                    self.access_token = token_data['access_token']
                    self.token_expiration = datetime.datetime.fromisoformat(token_data['time'])
                else:
                    self.refresh_token()
        else:
            self.refresh_token()

    def save_token(self):
        with open(self.token_path, 'w') as f:
            token_data = {
                'access_token': self.access_token,
                'time': self.token_expiration.isoformat()
            }
            json.dump(token_data, f)

    def refresh_token(self):
        headers = {"content-type": "application/json"}
        body = {"grant_type": "client_credentials",
                "appkey": self.app_key,
                "appsecret": self.app_secret}
        path = "oauth2/tokenP"
        url = f"{self.url_base}/{path}"
        res = requests.post(url, headers=headers, data=json.dumps(body))
        self.access_token = res.json()["access_token"]
        self.token_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.save_token()

    def send_dico(self, msg): #
        now = datetime.datetime.now()
        message = {'content': f"[{now.strftime('%Y/%m/%d %H:%M:%S')}] {str(msg)}"}
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)
        with open(f"{self.log_path}/log{now.strftime('%Y%m%d')}.txt", 'a') as f:
            f.write(msg + '\n')
        requests.post(self.webhook_url, data=message)
        print(message)

    def hashkey(self, data):
        path = "uapi/hashkey"
        url = f"{self.url_base}/{path}"
        headers = {
            'content-Type': 'application/json',
            'appKey': self.app_key,
            'appSecret': self.app_secret,
        }
        res = requests.post(url, headers=headers, data=json.dumps(data))
        return res.json()["HASH"]

    def current_price(self, market, code):
        path = "/uapi/overseas-price/v1/quotations/price"
        url = f"{self.url_base}/{path}"
        headers = {
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "HHDFS00000300"
        }
        params = {"AUTH": "", "EXCD": market, "SYMB": code}
        res = requests.get(url, headers=headers, params=params)
        self.send_dico(f"[현재가] {code} : {res.json()['output']['last']} ")
        return float(res.json()['output']['last'])

    def buy(self, market, code, qty, price):
        path = "uapi/overseas-stock/v1/trading/order"
        URL = f"{self.url_base}/{path}"
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": market,
            "PDNO": code,
            "ORD_DVSN": "00",
            "ORD_QTY": str(int(qty)),
            "OVRS_ORD_UNPR": f"{round(price,2)}",
            "ORD_SVR_DVSN_CD": "0"
            }
        header = {"authorization":f"Bearer {self.access_token}",
                "appkey":self.app_key,
                "appsecret" : self.app_secret,
                "tr_id":"TTTT1002U",
                "hashkey" : self.hashkey(body)}
        res = requests.post(URL, headers=header, data=json.dumps(body))
        self.send_dico(f"[매수 시도] {code} {qty}주 ${price}")
        if res.json()['rt_cd'] == '0':
            self.send_dico(f"[매수 성공]{str(res.json()['msg1'])}")
            return 0
        else:
            self.send_dico(f"[매수 실패]{str(res.json()['msg1'])}")
            return 1

    def sell(self, market, code, qty, price):
        path = "uapi/overseas-stock/v1/trading/order"
        URL = f"{self.url_base}/{path}"
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": market,
            "ORD_QTY" : qty,
            "PDNO": code,
            "ORD_DVSN": "00",
            "OVRS_ORD_UNPR": f"{round((price),2)}",
            "ORD_SVR_DVSN_CD": "0"
        }
        header = {
            "authorization":f"Bearer {self.access_token}",
            "appKey":self.app_key,
            "appSecret":self.app_secret,
            "tr_id":"TTTT1006U",
            "custtype":"P",
            "hashkey" : self.hashkey(body)
        }
        res = requests.post(URL, headers=header, data=json.dumps(body))
        self.send_dico(f"[매도 시도] {code} {qty}주 ${price}")
        if res.json()['rt_cd'] == '0':
            self.send_dico(f"[매도 성공]{str(res.json()['msg1'])}")
            return True
        else:
            self.send_dico(f"[매도 실패]{str(res.json()['msg1'])}")
            return False

    def total_stock_balance(self):
        path = "uapi/overseas-stock/v1/trading/inquire-balance"
        URL = f"{self.url_base}/{path}"
        headers = {"Content-Type":"application/json",
            "authorization":f"Bearer {self.access_token}",
            "appKey":self.app_key,
            "appSecret":self.app_secret,
            "tr_id":"JTTT3012R",
            "custtype":"P"
        }
        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": "NASD",
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        res = requests.get(URL, headers=headers, params=params)
        output1=res.json()['output1']
        output2=res.json()['output2']
        self.send_dico(f"=================주식 잔고================")
        for stock in output1:
            if int(stock['ovrs_cblc_qty'])>0:
                self.send_dico(f"{stock['ovrs_pdno']}  {stock['ovrs_item_name']}  {stock['ovrs_cblc_qty']}주")
                self.send_dico(f"[평단가] ${stock['pchs_avg_pric']} [현재가] ${stock['ovrs_stck_evlu_amt']}")
                self.send_dico(f"[평가손익] ${stock['frcr_evlu_pfls_amt']}  [평가손익율] {stock['evlu_pfls_rt']}%")
                self.send_dico("-----------------------------------------")

                stock_code,stock_qty = [entry["ovrs_pdno"] for entry in output1 if entry["ovrs_pdno"] != "ARAV"],stock['ovrs_cblc_qty']
        self.send_dico(f"=================총주식 잔고================")
        self.send_dico(f"[총평가손익금액] : ${output2['tot_evlu_pfls_amt']} [해외총손익] : ${output2['ovrs_tot_pfls']} [총수익률] : {output2['tot_pftrt']}%")
        return stock_code,stock_qty #잔고 수량 #잔고 코드

    def part_stock_balance(self, code):
        path = "uapi/overseas-stock/v1/trading/inquire-balance"
        URL = f"{self.url_base}/{path}"
        headers = {"Content-Type":"application/json",
            "authorization":f"Bearer {self.access_token}",
            "appKey":self.app_key,
            "appSecret":self.app_secret,
            "tr_id":"JTTT3012R",
            "custtype":"P"
        }
        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": "NASD",
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        res = requests.get(URL, headers=headers, params=params)
        output1=res.json()['output1']
        print(output1)
        for stock in output1:
            if stock['ovrs_pdno'] == code:

                return stock

    def how_buy(self, market,code,price):
        path = "/uapi/overseas-stock/v1/trading/inquire-psamount"
        URL = f"{self.url_base}/{path}"
        headers = {
            "authorization":f"Bearer {self.access_token}",
            "appKey":self.app_key,
            "appSecret":self.app_secret,
            "tr_id":"TTTS3007R"
        }
        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": "NASD",
            "OVRS_ORD_UNPR": price,
            "ITEM_CD": code
        }
        res = requests.get(URL, headers=headers, params=params)
        res = res.json()['output']
        self.send_dico(f"보유 외화 ${res['ord_psbl_frcr_amt']} {code} ${price} {res['max_ord_psbl_qty']}주 구매가능")
        bill, qty = res['ord_psbl_frcr_amt'], res['max_ord_psbl_qty']
        return float(bill), int(float(qty)) #주문가능외확금액 # 주문 가능 수량

    def order_cancel(self, market, code, ODNO, qty):
        path = "/uapi/overseas-stock/v1/trading/order-rvsecncl"
        URL = f"{self.url_base}/{path}"
        header = {
            "authorization": f"Bearer {self.access_token}",
            "appKey": self.app_key,
            "appSecret": self.app_secret,
            "tr_id": "TTTT1004U"
        }
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": "NASD",
            "PDNO": code,
            "ORGN_ODNO": ODNO,
            "RVSE_CNCL_DVSN_CD": "02",
            "ORD_QTY": qty,
            "OVRS_ORD_UNPR": "0"
        }
        res = requests.post(URL, headers=header, json=body)
        if res.status_code == 200:
            self.send_dico(f"[미체결 주문 취소] : {code}, {ODNO}, {qty}")
        else:
            print(f"주문 취소 실패 - 응답 코드: {res.status_code}, 응답 내용: {res.text}")

    def order_correct(self, market, code, qty, price, ODNO): #오더 정정
        path = "uapi/overseas-stock/v1/trading/order"
        URL = f"{self.url_base}/{path}"
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": "NASD",
            "PDNO": code,
            "ORGN_ODNO" : ODNO,
            "RVSE_CNCL_DVSN_CD": "01",
            "ORD_QTY": str(int(qty)),
            "OVRS_ORD_UNPR": f"{round((price),2)}",
            "ORD_SVR_DVSN_CD": "price"
        }
        header = {
            "authorization":f"Bearer {self.access_token}",
            "appKey":self.app_key,
            "appSecret":self.app_secret,
            "tr_id":"TTTT1004U",
            "custtype":"P",
            "hashkey" : self.hashkey(body)
        }
        res = requests.post(URL, headers=header,params=body)
        if res.json["rt_cd"] == "0":
            self.send_dico(f"{code} {qty}주 ${price} 주문 정정 완료")
            return True

    def order_unfilled(self): #미체결 내역 조회
        path = "/uapi/overseas-stock/v1/trading/inquire-nccs"
        URL = f"{self.url_base}/{path}"
        header = {
            "authorization":f"Bearer {self.access_token}",
            "appKey":self.app_key,
            "appSecret":self.app_secret,
            "tr_id":"TTTS3018R"
        }
        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": "NASD",
            "SORT_SQN" : "DS",
            "CTX_AREA_FK200":"",
            "CTX_AREA_NK200":""
        }
        res = requests.get(URL, headers=header, params=params).json()
        odno = [order1['odno'] for order1 in res['output']]
        code = [order2['pdno'] for order2 in res['output']]
        qty = [order3['nccs_qty'] for order3 in res['output']]
        price = [order4['ft_ord_unpr3'] for order4 in res['output']]
        self.send_dico(f"[미체결 주문 조회] : {code}, {qty}, {price}, {odno}")
        return code, qty, price, odno

    def STOCK_DATA(self, code, start):
        path = '/uapi/overseas-price/v1/quotations/dailyprice'
        URL = f"{self.url_base}/{path}"
        header = {"authorization":f"Bearer {self.access_token}",
                "appkey" : self.app_key,"appsecret":self.app_secret,
                "tr_id" : "HHDFS76240000"
                }
        params = {
                "AUTH" : "",
                "EXCD" : "NAS",
                "SYMB" : code,
                "GUBN" : "0",
                "BYMD" : start,
                "MODP" : "1"
                }
        res = requests.get(URL, headers=header, params=params)
        return res.json()['output2']

    def INDEX_DATA(self, code, start, end):
        path = '/uapi/overseas-price/v1/quotations/inquire-daily-chartprice'
        URL = f"{self.url_base}/{path}"
        header = {"authorization":f"Bearer {self.access_token}",
                "appkey" : self.app_key,"appsecret":self.app_secret,
                "tr_id" : "FHKST03030100"
                }
        params = {"FID_INPUT_ISCD" : code,
                "FID_COND_MRKT_DIV_CODE" : "N",
                "FID_PERIOD_DIV_CODE" : "D",
                "FID_INPUT_DATE_1" : start,
                "FID_INPUT_DATE_2" : end
                }
        res = requests.get(URL, headers=header, params=params)
        return res.json()['output2']

    def EXCHANGE_DATA(self, code, start, end):
        path = '/uapi/overseas-price/v1/quotations/inquire-daily-chartprice'
        URL = f"{self.url_base}/{path}"
        header = {"authorization":f"Bearer {self.access_token}",
                "appkey" : self.app_key,"appsecret":self.app_secret,
                "tr_id" : "FHKST03030100"
                }
        params = {"FID_INPUT_ISCD" : code,
                "FID_COND_MRKT_DIV_CODE" : "X",
                "FID_PERIOD_DIV_CODE" : "D",
                "FID_INPUT_DATE_1" : start,
                "FID_INPUT_DATE_2" : end
                }
        res = requests.get(URL, headers=header, params=params)
        return res.json()['output2']

class marketmanager:
    def __init__(self):
            self.market_codes = {
                'NYSE': 'NYS',
                'NASD': 'NAS',
                'AMEX': 'AMS'
            }
            self.stock_codes = {
                    'AAPL': 'NASD',
                    'MSFT': 'NASD',
                    'TSLA': 'NASD',
                    'IBM': 'NYSD',
                    'GOOGL': 'NASD',
                    'AMZN': 'NASD'
                }

    def nas2nasd(self, market_code):
        return self.market_codes.get(market_code)

    def aapl2nasd(self, code):
        return self.stock_codes.get(code)

class balance:
    def __init__(self, api, cash_bal, log_name = 'test'):
        self.api = api() #api 호출
        self.stock_bal = {} #주식 잔고
        self.cash_bal = cash_bal # 현금잔고
        self.tax = 0.0119  #거래 수수료
        self.mm = marketmanager()
        self.log = []
        self.log_dir = f'log/bal/{log_name}'
    
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def make_log(self, code, price, qty, type):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = f"""{now} {code} ${price:.2f} {qty}주 {type} ${self.cash_bal:.2f} {self.format()}"""
        print(msg)
        now = datetime.datetime.now().strftime('%Y-%m-%d')
        with open(f"{self.log_dir}/log{now}.txt", 'a') as f:
            f.write(msg + '\n')

    def make_csv(self, code, qty, price, type):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = f"{now}, {code}, {qty}, {price}, {type}, {self.cash_bal}, "
        with open(f"{self.log_dir}/scv.txt", 'a') as f:
            f.write(msg + '\n')


    def buy_update(self, code, qty, price):
        if code in self.stock_bal:
            self.stock_bal[code]['qty'] += qty #매수 개수
            self.stock_bal[code]['price'] = price # 매수 가격
        else:
            self.stock_bal[code] = {'qty': qty, 'price': price}
        self.cash_bal -= price * qty * (1+self.tax) #현금 차감 +수수료
        self.make_log(code, price, qty, 'buy')

    def sell_update(self, code, qty, price):      
        if self.stock_bal[code]['qty'] >= qty:
            self.stock_bal[code]['qty'] -= qty #매도 개수
            self.stock_bal[code]['price'] = price # 매도 가격
            self.cash_bal += price * qty * (1-self.tax) #현금 차감 +수수료
        if self.stock_bal[code]['qty'] == 0:
            del self.stock_bal[code]
        self.make_log(code, price, qty, 'sell')

    def buy_stock(self, code, qty, price):        
        if self.cash_bal < price * qty * (1+self.tax):
            self.make_log(code, qty, price, 'buy_eng')
        else: # 매수 실행
            market = self.mm.aapl2nasd(code)
            result = 0#self.api.buy(market, code, qty, price)
            if result == 0:
                self.buy_update(code, qty, price)
            else:
                self.make_log(code, qty, price, 'fail_api')

    def sell_stock(self, code, qty, price):
        if code not in self.stock_bal or self.stock_bal[code]['qty'] < qty: #잔고 확인
            self.make_log(code, qty, price, 'sell_fail')
            return 
        # 매도 실행
        market = self.mm.aapl2nasd(code)
        result = 0# self.api.sell(market, code, qty, price)
        if result == 0:
            self.sell_update(code, qty, price)
        else:
            self.make_log(code, qty, price, 'fail_api')

    def total_val(self):
        total_stock = sum(self.api.currnet_price(code) * qty['qty'] for code, qty in self.stock_bal.item())
        total_val = total_stock + self.cash_bal
        return ",".join(f"{total_val}")

    def format(self):
        return ", ".join(f"{stock}: {details['qty']}주" for stock, details in self.stock_bal.items())



test1 = balance(api, 100, log_name = 'test1')
for i in range(10):
    test1.buy_stock('AAPL',10, 9)
    test1.sell_stock('AAPL',10,9 )







# 생각노트
# 각 계좌별 구매 code 후보에 따른 marketmanager 추가
# 자산 가격 변동을 위한 로그
# 포트폴리오 변동 차트
# 포트폴리오 = total_bal 만들기