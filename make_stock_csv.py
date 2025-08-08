from koreapi import api, logger
import os
import pandas as pd
from datetime import datetime, timedelta

class data_loader:
    
    '''
    목적
    원하는 날짜, 원하는 기간의 데이터를 조회 및 축적 할 수 있다.
    '''

    def __init__ (self):
        self.api = api()
        self.logger = logger()
    
    def load_m_data(self, code, min = 1):
        date = datetime.now().strftime("%Y%m%d%H%M%S")
        csv_path = 'log/csv/m_csv'
        file_path = os.path.join(csv_path, f'{code}_data.csv')
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)

        if os.path.isfile(file_path):
            df_existing = pd.read_csv(file_path)
            df_existing['datetime'] = pd.to_datetime(df_existing['datetime'])
            last_updated_date = df_existing['datetime'].iloc[-1].strftime("%Y%m%d%H%M%S")
        else: 
            df_existing = pd.DataFrame()
            last_updated_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d%H%M%S")
        
        while True:
            print(date, last_updated_date)
            df = pd.DataFrame(self.api.M_STOCK_DATA(code, min, date))
            if df.empty:
                self.logger.send_dico(f"{code} 받은 데이터가 없음")
                break

            df = df[['xymd', 'xhms', 'open', 'high', 'low', 'last']]
            date = df['xymd'].iloc[-1] + df['xhms'].iloc[-1]
            df['datetime'] = pd.to_datetime(df['xymd'] + df['xhms'], format='%Y%m%d%H%M%S')
            df.drop(columns=['xymd', 'xhms'], inplace=True)
            df = df[['datetime','open', 'high','low','last']]
            
            df_existing = pd.concat([df_existing, df])
            
            if int(date) <= int(last_updated_date):
                self.logger.send_dico(f"{code} min={min}/{last_updated_date}~{date} 가져오기 완료 ")
                break 

        df_existing = df.drop_duplicates().sort_values(by='datetime').reset_index(drop=True)
        df_existing.to_csv(file_path, index=False)

test = data_loader()
test.load_m_data('AAPL')