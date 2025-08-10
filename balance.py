from koreapi import korea_api, logger
import os
import datetime
import pandas as pd
import csv

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
        self.csv_path = f'log/bal/{self.name}'
        self.file_path = os.path.join(self.csv_path, f'{self.name}_log.csv')
        self._initialize_csv()

        #가상 계좌 기본 설정
        self.stock_bal = {'AAPL': {'qty': 10, 'avg_price': 150.0}} #stock balance
        self.cash_bal = float(initial_cash) # cash balance
        self.tax = 0.0009  #거래 수수료
        self.pnl = 0.0

    def buy(self, code, qty, price): #주식 사고 팔기
        #일반 계좌에 팔 수 있나 확인
        #아니면 오류

        if self.cash_bal > qty*price:
            self.api.sell(code, qty, price)
        
        return 0

    def sell(self, code, qty, price):
        if self.stock_bal[code]['qty'] > qty:
            if self.api.sell(code, qty, price):
                return 0

        return 0
    
    def total_value(self):
        stock_val = 0
        for symbol, data in self.stock_bal.items():
            stock_val += data['qty'] * self.api.current_price(symbol)
        return stock_val + self.cash_bal
    
    def unreal_pnl(self, ):
        return 0
    

    #로그 처리 부분
    def _initialize_csv(self, ):
        if not os.path.exists(self.csv_path):
            os.makedirs(self.csv_path)

        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.columns)

    def _add_log(self, type, code, qty, price, tax, pnl=0.0):
        log_data = [
            datetime.datetime.now().isoformat(),
            type,
            code,
            qty,
            price,
            tax,
            pnl
        ]

        with open(self.file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(log_data)
        self.logger.send_dico(log_data)




if __name__=="__main__":
    model_a = balance(name='model_a', initial_cash=10000)
    
    model_a._add_log('sell','aapl',3,100,1,1) # 거래 발생 시 빠르게 기록

    model_a.buy(1,1,1)