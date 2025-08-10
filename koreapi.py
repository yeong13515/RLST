import yaml
import json
import requests
import datetime
import os

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
                    'AMZN': 'NASD',
                    'SOXS' : 'AMEX',
                    'SOXL' : 'AMEX',
                    'TQQQ' : 'NASD',
                    'SQQQ' : 'NASD',
                }

    def nasd2nas(self, market_code):
        return self.market_codes.get(market_code)

    def aapl2nasd(self, code):
        return self.stock_codes.get(code)
    
class logger:
    def __init__ (self, config_path='ignore/config.yaml', log_path = 'log/api'):
        with open(config_path, encoding='UTF-8') as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
        self.webhook_url = cfg['DISCORD_WEBHOOK_URL']
        self.log_path = log_path

    def send_dico(self, msg): 
        now = datetime.datetime.now()
        message = {'content': f"[{now.strftime('%Y/%m/%d %H:%M:%S')}] {str(msg)}"}
        msg = f'[{now}] {(msg)}'
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)
        with open(f"{self.log_path}/log{now.strftime('%Y%m%d')}.txt", 'a') as f:
            f.write(msg + '\n')
        requests.post(self.webhook_url, data=message)
        print(message)

class api: #api 클래스
    def __init__(self, config_path='ignore/config.yaml', token_path='ignore/token.dat'):
        self.load_config(config_path)
        self.token_path = token_path
        self.access_token = ""
        self.token_expiration = None
        self.load_token()
        self.logger = logger()
        self.mm = marketmanager()

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
        self.logger.send_dico(f"[현재가] {code} : {res.json()['output']['last']} ")
        return float(res.json()['output']['last'])

    def buy(self, code, qty, price):
        market = self.mm.aapl2nasd(code)
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
        self.logger.send_dico(f"[매수 시도] {code} {qty}주 ${price}")
        if res.json()['rt_cd'] == '0':
            self.logger.send_dico(f"[매수 성공]{str(res.json()['msg1'])}")
            return 0
        else:
            self.logger.send_dico(f"[매수 실패]{str(res.json()['msg1'])}")
            return 1

    def sell(self, market, code, qty, price):
        market = self.mm.aapl2nasd(code)
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
        self.logger.send_dico(f"[매도 시도] {code} {qty}주 ${price}")
        if res.json()['rt_cd'] == '0':
            self.logger.send_dico(f"[매도 성공]{str(res.json()['msg1'])}")
            return True
        else:
            self.logger.send_dico(f"[매도 실패]{str(res.json()['msg1'])}")
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
        self.logger.send_dico(f"=================주식 잔고================")
        for stock in output1:
            if int(stock['ovrs_cblc_qty'])>0:
                self.logger.send_dico(f"{stock['ovrs_pdno']}  {stock['ovrs_item_name']}  {stock['ovrs_cblc_qty']}주")
                self.logger.send_dico(f"[평단가] ${stock['pchs_avg_pric']} [현재가] ${stock['ovrs_stck_evlu_amt']}")
                self.logger.send_dico(f"[평가손익] ${stock['frcr_evlu_pfls_amt']}  [평가손익율] {stock['evlu_pfls_rt']}%")
                self.logger.send_dico("-----------------------------------------")

                stock_code,stock_qty = [entry["ovrs_pdno"] for entry in output1 if entry["ovrs_pdno"] != "ARAV"],stock['ovrs_cblc_qty']
        self.logger.send_dico(f"=================총주식 잔고================")
        self.logger.send_dico(f"[총평가손익금액] : ${output2['tot_evlu_pfls_amt']} [해외총손익] : ${output2['ovrs_tot_pfls']} [총수익률] : {output2['tot_pftrt']}%")
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

    def how_buy(self, code,price):
        market = self.mm.nasd2nas(self.mm.aapl2nasd(code))
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
            "OVRS_EXCG_CD": market,
            "OVRS_ORD_UNPR": price,
            "ITEM_CD": code
        }
        res = requests.get(URL, headers=headers, params=params)
        res = res.json()['output']
        self.logger.send_dico(f"보유 외화 ${res['ord_psbl_frcr_amt']} {code} ${price} {res['max_ord_psbl_qty']}주 구매가능")
        bill, qty = res['ord_psbl_frcr_amt'], res['max_ord_psbl_qty']
        return float(bill), int(float(qty)) #주문가능외확금액 # 주문 가능 수량

    def order_cancel(self, code, ODNO, qty):
        market = self.mm.nasd2nas(self.mm.aapl2nasd(code))
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
            "OVRS_EXCG_CD": market,
            "PDNO": code,
            "ORGN_ODNO": ODNO,
            "RVSE_CNCL_DVSN_CD": "02",
            "ORD_QTY": qty,
            "OVRS_ORD_UNPR": "0"
        }
        res = requests.post(URL, headers=header, json=body)
        if res.status_code == 200:
            self.logger.send_dico(f"[미체결 주문 취소] : {code}, {ODNO}, {qty}")
        else:
            print(f"주문 취소 실패 - 응답 코드: {res.status_code}, 응답 내용: {res.text}")

    def order_correct(self, code, qty, price, ODNO): #오더 정정
        market = self.mm.nasd2nas(self.mm.aapl2nasd(code))
        path = "uapi/overseas-stock/v1/trading/order"
        URL = f"{self.url_base}/{path}"
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "OVRS_EXCG_CD": market,
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
            self.logger.send_dico(f"{code} {qty}주 ${price} 주문 정정 완료")
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
        self.logger.send_dico(f"[미체결 주문 조회] : {code}, {qty}, {price}, {odno}")
        return code, qty, price, odno

    def D_STOCK_DATA(self, code, start):
        market = self.mm.nasd2nas(self.mm.aapl2nasd(code))
        path = '/uapi/overseas-price/v1/quotations/dailyprice'
        URL = f"{self.url_base}/{path}"
        header = {"authorization":f"Bearer {self.access_token}",
                "appkey" : self.app_key,"appsecret":self.app_secret,
                "tr_id" : "HHDFS76240000"
                }
        params = {
                "AUTH" : "",
                "EXCD" : market,
                "SYMB" : code,
                "GUBN" : "0",
                "BYMD" : start,
                "MODP" : "1"
                }
        res = requests.get(URL, headers=header, params=params)
        
        if 'output2' in res.json():
            return res.json()['output2']
        else:
            return None

    def M_STOCK_DATA(self, code, min, date):
        market = self.mm.nasd2nas(self.mm.aapl2nasd(code))
        path = '/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice'
        URL = f"{self.url_base}/{path}"
        header = {"authorization":f"Bearer {self.access_token}",
                "appkey" : self.app_key,"appsecret":self.app_secret,
                "tr_id" : "HHDFS76950200"
                }
        params = {
                "AUTH":"",
                "EXCD":market,
                "SYMB":code,
                "NMIN":min,
                "PINC":"1",
                "NEXT":"1",
                "NREC":"120",
                "FILL":"",
                "KEYB": date
                }
        res = requests.get(URL, headers=header, params=params)
        #print(res.json())
        if 'output2' in res.json():
            return res.json()['output2']
        else:
            return None

    def D_INDEX_DATA(self, code, end):
        path = '/uapi/overseas-price/v1/quotations/inquire-daily-chartprice'
        URL = f"{self.url_base}/{path}"
        header = {"authorization":f"Bearer {self.access_token}",
                "appkey" : self.app_key,"appsecret":self.app_secret,
                "tr_id" : "FHKST03030100"
                }
        params = {"FID_INPUT_ISCD" : code,
                "FID_COND_MRKT_DIV_CODE" : "N",
                "FID_PERIOD_DIV_CODE" : "D",
                "FID_INPUT_DATE_1" : end,
                "FID_INPUT_DATE_2" : ""  #start 쓸수도 있음
                }
        res = requests.get(URL, headers=header, params=params)
        #print(res.json())
        if 'output2' in res.json():
            return res.json()['output2']
        else:
            return None


if __name__=="__main__":
    test = api()
    print(test.D_INDEX_DATA('.DJT', 20200101))
    

# 생각노트
# 각 계좌별 구매 code 후보에 따른 marketmanager 추가
# 자산 가격 변동을 위한 로그
# 포트폴리오 변동 차트
# 포트폴리오 = total_bal 만들기

# 급등주 찾기 프로젝트
# 분봉 단타 프로젝트
# 강화학습 나스닥 거래
# 여론을 통한 주식 투자

# 카카오톡 오픈톡으로 디코 대체
# 티스토리 자동 업로드. 