from rlst.core.koreapi import korea_api, logger
import os
import pandas as pd
from datetime import datetime, timedelta
import time
import config

class stock_data_loader:
    '''
    목적
    원하는 날짜, 원하는 기간의 데이터를 조회 및 축적 할 수 있다.

    load_m_data : 분 단위 (최대 현 시점으로 부터 1개월)
    load_d_data : 일 단위 
    load_index_data : 일 단위 index
    '''

    def __init__ (self, api=korea_api(), logger = logger()):
        self.api = api
        self.logger = logger
    
    def load_m_data(self, code, min = 1, tick=False):
        '''
        오늘부터 약 1개월까지 min단위 조회

        초당 거래횟수제한으로 큰 데이터 받을 시 tick 사용
        '''
        date = start = datetime.now().strftime("%Y%m%d%H%M%S")
        csv_path = config.RAW_DATA_DIR/'m_csv' 
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
                self.logger.send_dico(f"{code} {date} 받은 데이터가 없음")
                break

            df = df[['xymd', 'xhms', 'open', 'high', 'low', 'last']]
            oldest_date_str = df['xymd'].min() + df['xhms'].min()
            df['datetime'] = pd.to_datetime(df['xymd'] + df['xhms'], format='%Y%m%d%H%M%S')
            df.drop(columns=['xymd', 'xhms'], inplace=True)
            df = df[['datetime','open', 'high','low','last']]
            
            df_existing = pd.concat([df_existing, df])
            
            if int(date) <= int(last_updated_date):
                break 
            oldest_date_obj = pd.to_datetime(oldest_date_str, format='%Y%m%d')
            date = (oldest_date_obj - timedelta(days=1)).strftime('%Y%m%d')
            
            if tick: #초당거래횟수 제한으로 0.1 틱
                time.sleep(0.2)

        df_existing = df_existing.drop_duplicates().sort_values(by='datetime').reset_index(drop=True)
        df_existing.to_csv(file_path, index=False)
        self.logger.send_dico(f"{code} {last_updated_date}~{start} 저장 완료 ")

    def load_d_data(self, code, target_date = 20150101):
        '''
        일자 데이터 조회
        target_date = 20150101
        '''
        start = date = datetime.now().strftime("%Y%m%d")
        csv_path = config.RAW_DATA_DIR/'d_csv'
        file_path = os.path.join(csv_path, f'{code}_data.csv')
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)

        if os.path.isfile(file_path):
            df_existing = pd.read_csv(file_path)
            df_existing['datetime'] = pd.to_datetime(df_existing['datetime'])
            last_updated_date = df_existing['datetime'].iloc[-1].strftime("%Y%m%d")
        else: 
            df_existing = pd.DataFrame()
            last_updated_date = target_date
        
        while True:
            print(date, last_updated_date)
            df = pd.DataFrame(self.api.D_STOCK_DATA(code, date))
            if df.empty:
                self.logger.send_dico(f"{code} {date} 받은 데이터가 없음")
                break

            df = df[['xymd', 'open', 'high', 'low', 'clos', 'tvol']]
            oldest_date_str  = df['xymd'].min()
            df['datetime'] = pd.to_datetime(df['xymd'], format='%Y%m%d')
            df.drop(columns=['xymd'], inplace=True)
            df = df[['datetime','open', 'high','low','clos', 'tvol']]
            
            df_existing = pd.concat([df_existing, df])
            if int(date) <= int(last_updated_date):
                break 
            oldest_date_obj = pd.to_datetime(oldest_date_str, format='%Y%m%d')
            date = (oldest_date_obj - timedelta(days=1)).strftime('%Y%m%d')

        self.logger.send_dico(f"{code} {last_updated_date}~{start} 저장 완료 ")
        df_existing = df_existing.drop_duplicates().sort_values(by='datetime').reset_index(drop=True)
        df_existing.to_csv(file_path, index=False)


    def load_index_data(self, code, target_date=20150101, tick = False):
        '''
        일자 데이터 조회
        target_date = 20150101
        '''
        start = date = datetime.now().strftime("%Y%m%d")
        csv_path = config.RAW_DATA_DIR/'index_csv'
        file_path = os.path.join(csv_path, f'{code}_data.csv')
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)

        if os.path.isfile(file_path):
            df_existing = pd.read_csv(file_path)
            df_existing['datetime'] = pd.to_datetime(df_existing['datetime'])
            last_updated_date = df_existing['datetime'].iloc[-1].strftime("%Y%m%d")
        else: 
            df_existing = pd.DataFrame()
            last_updated_date = target_date
        
        while True:
            print(date, last_updated_date)
            df = pd.DataFrame(self.api.D_INDEX_DATA(code, date))
            if df.empty:
                self.logger.send_dico(f"{code} {date} 받은 데이터가 없음")
                break

            df = df[['stck_bsop_date', 'ovrs_nmix_oprc', 'ovrs_nmix_hgpr', 'ovrs_nmix_lwpr', 'ovrs_nmix_prpr', 'acml_vol']]
            date = df['stck_bsop_date'].min()
            df['datetime'] = pd.to_datetime(df['stck_bsop_date'], format='%Y%m%d')
            df.drop(columns=['stck_bsop_date'], inplace=True)
            df = df[['datetime','ovrs_nmix_oprc', 'ovrs_nmix_hgpr','ovrs_nmix_lwpr','ovrs_nmix_prpr', 'acml_vol']]
            
            df_existing = pd.concat([df_existing, df])
            if int(date) <= int(last_updated_date):
                break 
            
            if tick: #초당거래횟수 제한으로 0.1 틱
                time.sleep(0.2)
        
        self.logger.send_dico(f"{code} {last_updated_date}~{start} 저장 완료 ")
        df_existing = df_existing.drop_duplicates().sort_values(by='datetime').reset_index(drop=True)
        df_existing.to_csv(file_path, index=False)


