from koreapi import api, logger
import os
import datetime

class balance:
    def __init__(self,api, cash_bal, log_name = 'test'):
        self.api = api() #api 호출
        self.stock_bal = {} #주식 잔고
        self.cash_bal = cash_bal # 현금잔고
        self.tax = 0.0009  #거래 수수료
        self.log = []
        self.log_dir = f'log/bal/{log_name}'
        self.logger = logger()
    
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def make_log(self, code, price, qty, type):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = f"""{now} {code} ${price:.2f} {qty}주 {type} ${self.cash_bal:.2f} {self.format()}, ${self.total_val():.2f}"""  
        self.logger.send_dico(f"""{code} ${price:.2f} {qty}주 {type} ${self.cash_bal:.2f} {self.format()}, ${self.total_val():.2f}""")
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
            self.make_log(code, qty, price, 'fail_egh')
        else: # 매수 실행
            
            result = 0 #self.api.buy(code, qty, price) #삭제
            if result == 0:
                self.buy_update(code, qty, price)
            else:
                self.make_log(code, qty, price, 'fail_api')

    def sell_stock(self, code, qty, price):
        if code not in self.stock_bal or self.stock_bal[code]['qty'] < qty: #잔고 확인
            self.make_log(code, qty, price, 'fail_qty')
            return 
        # 매도 실행
        result = 0# self.api.sell(code, qty, price)
        if result == 0:
            self.sell_update(code, qty, price)
        else:
            self.make_log(code, qty, price, 'fail_api')

    def total_val(self):
        #total_stock = sum(self.api.current_price(code) * qty['qty'] for code, qty in self.stock_bal.items())
        total_stock = sum(9 * qty['qty'] for code, qty in self.stock_bal.items()) #삭제할것
        total_val = total_stock + self.cash_bal
        return total_val

    def format(self):
        return ", ".join(f"{stock}: {details['qty']}주" for stock, details in self.stock_bal.items())

