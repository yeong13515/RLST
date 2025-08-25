from rlst.core.koreapi import korea_api, logger
import os
import datetime
import pandas as pd
import csv, json
import config

class balance:
    def __init__(self, name, initial_cash,api=korea_api(), logger=logger()):
        '''
        구현 목표

        0. 가상 주식 계좌로 여러 모델을 한 계좌에서 돌리기 위함. 

        1. stock holding & cash 현황
        2. trading log

        '''
        #의존
        self.api = api #api 호출
        self.logger = logger
        self.name = name

        #log
        self.columns = ['timestamp', 'type', 'symbol', 'qty', 'price', 'tax', 'pnl']
        self.base_path = config.LOG_DIR / f'bal/{self.name}'
        self.log_csv_path = os.path.join(self.base_path, f'{self.name}_log.csv')
        self.bal_json_path = os.path.join(self.base_path, f'{self.name}_bal.json')

        self.initial_cash = initial_cash
        self.tax = 0.0009  #거래 수수료
        self.pnl = 0.0

        self._initialize_()


    def buy(self, code, qty, price): #주식 사고 팔기
        if self.stock_bal['cash'] > qty*price*(1+self.tax): #cash 확인
            if True : #self.api.sell(code, qty, price): #여기 실제 매수가 일어났나 확인하는 부분
                self.stock_bal['cash'] -= qty * price * (1+self.tax)
                
                if code in self.stock_bal['stock'] and self.stock_bal['stock'][code]['qty'] > 0:
                    self.stock_bal['stock'][code]['avg_price']=(self.stock_bal['stock'][code]['avg_price']*self.stock_bal['stock'][code]['qty'] + qty*price ) /( qty + self.stock_bal['stock'][code]['qty'] )
                    self.stock_bal['stock'][code]['qty'] += qty
                else:
                    self.stock_bal['stock'][code] = {'qty': qty, 'avg_price': price}
            
                self._add_log('buy', code, qty, price, qty*price*self.tax)
            else:
                self.logger.send_dico('api 매도 실패')
        else:
            self.logger.send_dico('qty 매도 실패')
        print(self.stock_bal)


    def sell(self, code, qty, price):
        if code in self.stock_bal['stock'] and self.stock_bal['stock'][code]['qty'] >= qty: #qty 확인
            if True : #self.api.sell(code, qty, price): #여기 실제 매도가 일어났나 확인하는 부분
                self.stock_bal['cash'] += qty * price * (1 - self.tax)
                self.stock_bal['stock'][code]['qty'] -= qty

                pnl = round((price - self.stock_bal['stock'][code]['avg_price'])*qty * (1-self.tax), 2)
                self._add_log('sell', code, qty, price, qty*price*self.tax,pnl)
            else:
                self.logger.send_dico('api 매도 실패')
        else:
            self.logger.send_dico('qty 매도 실패')
        print(self.stock_bal)
    

    def total_value(self):
        stock_val = 0
        for symbol, data in self.stock_bal['stock'].items():
            stock_val += data['qty'] * self.api.current_price(symbol)
        return stock_val + self.stock_bal['cash']
    
    def unreal_pnl(self, ):
        for symbol, data in self.stock_bal['stock'].items():
            return (self.api.current_price(symbol) - data['avg_price'] ) * data['qty']  


    def _initialize_(self, ):
        # 로그 디렉토리 생성
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        
        #가상 계좌 기본 설정
        self.stock_bal = {
            'cash': self.initial_cash, 
            'stock': {}
        } 
        
        # 기존 bal.json 존재할 경우 불러오기
        if os.path.exists(self.bal_json_path):
            with open(f'{self.bal_json_path}', 'r', encoding='utf-8') as f:
                self.stock_bal = json.load(f)
        
        #log 파일 생성
        if not os.path.exists(self.log_csv_path):
            with open(self.log_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.columns)


    def _add_log(self, type, code, qty, price, tax, pnl=0.0):
        log_data = [datetime.datetime.now().isoformat(),type,code,qty,price,tax,pnl]

        with open(self.log_csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(log_data)

        with open(f'{self.bal_json_path}', 'w', encoding='utf-8') as f:
            json.dump(self.stock_bal, f, indent=4, ensure_ascii=False)


