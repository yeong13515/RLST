from koreapi import api, logger
import os
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


class csv_down:
    def __init__ (self, path = 'log/csv'):
        self.api = api()
        self.logger = logger()
        self.path = path
        self.columns = [
            'date', 'open', 'high', 'low', 'close', 'volume','close_ma5_ratio', 'close_ma10_ratio', 'close_ma20_ratio', 'close_ma60_ratio', 'close_ma120_ratio',
            'volume_ma5_ratio', 'volume_ma10_ratio', 'volume_ma20_ratio', 'volume_ma60_ratio', 'volume_ma120_ratio',
            'open_lastclose_ratio', 'high_close_ratio', 'low_close_ratio', 'close_lastclose_ratio', 'volume_lastvolume_ratio'
        ]

    def m_csv_api(self, code, min = '5'):
        csv_path = f'{self.path}/m_csv'
        file_path = os.path.join(csv_path, f'{code}_data.csv')

        if not os.path.exists(csv_path):
            os.makedirs(csv_path)

        df = pd.DataFrame(self.api.M_STOCK_DATA(code, min))
        df = df[['xymd', 'xhms', 'open', 'high', 'low', 'last']]

        if not df.empty:
            df['datetime'] = pd.to_datetime(df['xymd'] + ' ' + df['xhms'], format='%Y%m%d %H%M%S')
            df.drop(columns=['xymd', 'xhms'], inplace=True)
            df = df[['datetime','open', 'high','low','last']]
            if os.path.isfile(file_path):
                df_existing = pd.read_csv(file_path)
                df_existing['datetime'] = pd.to_datetime(df_existing['datetime'])
                df = pd.concat([df_existing, df])

            df = df.drop_duplicates().drop_duplicates(subset=['datetime']).sort_values(by=['datetime']).reset_index(drop=True)
            df.to_csv(file_path, index=False)
            return self.logger.send_dico(f"{code} m_csv donwload")

        return self.logger.send_dico(f"{code} m_csv fail")

    def d_csv_api(self, code, start):
        csv_path = f'{self.path}/d_csv'
        file_path = os.path.join(csv_path, f'{code}_data.csv')

        if not os.path.exists(csv_path):
            os.makedirs(csv_path)

        if os.path.isfile(file_path):
            df_existing = pd.read_csv(file_path)
            latest_date = str(df_existing['datetime'].max())
            start = datetime.strptime(latest_date,'%Y%m%d') + timedelta(days=1)
        else:
            df_existing = pd.DataFrame()
            start = datetime.strptime(start,'%Y%m%d')
            
        start = start + timedelta(days=60)
        today = datetime.now() +timedelta(days=60)

        while start < today:
            input = start.strftime('%Y%m%d')
            print(input)
            res = pd.DataFrame(self.api.D_STOCK_DATA(code, input))

            if res.empty or pd.isna(res['xymd']).all():
                self.logger.send_dico(f"{code} 상장일 이전 : {input}.")
                start = start + timedelta(days=60)
                continue

            res['datetime'] = res['xymd'].astype(int)
            df= res[['datetime','open','high','low','clos','tvol','tamt']]
            if not df_existing.empty:
                df_combined = pd.concat([df_existing, df]).drop_duplicates().reset_index(drop=True)
            else:
                df_combined = df

            today_str = datetime.now().strftime('%Y%m%d')
            df_combined = df_combined[df_combined['datetime'] < int(today_str)]

            df_combined = df_combined.drop_duplicates().drop_duplicates(subset=['datetime']).sort_values(by=['datetime']).reset_index(drop=True)
            df_combined.to_csv(file_path, index=False)

            start = start + timedelta(days=60)
            df_existing = df_combined
            self.logger.send_dico(f"{code} {start} ~  d_csv donwload")
        
    def market_api(self, code, type, start = '20100101'):
        csv_path = f'{self.path}/market_csv'
        file_path = os.path.join(csv_path, f'{code}_data.csv')

        if not os.path.exists(csv_path):
            os.makedirs(csv_path)

        if os.path.isfile(file_path):
            df_existing = pd.read_csv(file_path)
            latest_date = str(df_existing['datetime'].max())
            start = datetime.strptime(latest_date,'%Y%m%d') + timedelta(days=1)

        else:
            df_existing = pd.DataFrame()
            start = datetime.strptime(start,'%Y%m%d')
        end = start + timedelta(days=100)
        today = datetime.now()

        while start <= today:
            input_start, input_end = start.strftime('%Y%m%d'), end.strftime('%Y%m%d')
            res = pd.DataFrame(self.api.D_INDEX_DATA(code, type, input_start, input_end))

            if res.empty or pd.isna(res['stck_bsop_date']).all():
                self.logger.send_dico(f"{code} 상장일 이전 : {input_start}~ {input_end}.")
                start = start + timedelta(days=60)
                continue

            res['datetime'] = res['stck_bsop_date'].astype(int)
            df= res[['datetime','ovrs_nmix_oprc','ovrs_nmix_hgpr','ovrs_nmix_lwpr','ovrs_nmix_prpr']]
            if not df_existing.empty:
                df_combined = pd.concat([df_existing, df]).drop_duplicates().reset_index(drop=True)
            else:
                df_combined = df

            today_str = datetime.now().strftime('%Y%m%d')
            df_combined = df_combined[df_combined['datetime'] < int(today_str)]

            df_combined = df_combined.drop_duplicates().drop_duplicates(subset=['datetime']).sort_values(by=['datetime']).reset_index(drop=True)
            df_combined.to_csv(file_path, index=False)

            start, end = start + timedelta(days=100) , end + timedelta(days=100)
            df_existing = df_combined
            st , en = start , end
            self.logger.send_dico(f"{code} {st} ~ {en} market_data donwload")

    def preprocess(self, df):
        df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        
        windows = [5, 10, 20, 60, 120]
        for window in windows:
            df[f'close_ma{window}'] = df['close'].rolling(window).mean()
            df[f'volume_ma{window}'] = df['volume'].rolling(window).mean()
            df[f'close_ma{window}_ratio'] = (df['close'] - df[f'close_ma{window}']) / df[f'close_ma{window}']
            df[f'volume_ma{window}_ratio'] = (df['volume'] - df[f'volume_ma{window}']) / df[f'volume_ma{window}']
        
        df['open_lastclose_ratio'] = np.zeros(len(df))
        df.loc[1:, 'open_lastclose_ratio'] = (df['open'][1:].values - df['close'][:-1].values) / df['close'][:-1].values
        df['high_close_ratio'] = (df['high'].values - df['close'].values) / df['close'].values
        df['low_close_ratio'] = (df['low'].values - df['close'].values) / df['close'].values
        df['close_lastclose_ratio'] = np.zeros(len(df))
        df.loc[1:, 'close_lastclose_ratio'] = (df['close'][1:].values - df['close'][:-1].values) / df['close'][:-1].values
        df['volume_lastvolume_ratio'] = np.zeros(len(df))
        df.loc[1:, 'volume_lastvolume_ratio'] = (
            (df['volume'][1:].values - df['volume'][:-1].values) 
        / df['volume'][:-1].replace(0, np.nan).ffill().bfill().values)
        df['amount_lastamonut_ratio'] = np.zeros(len(df))
        df.loc[1:, 'amount_lastamonut_ratio'] = (
            (df['amount'][1:].values - df['amount'][:-1].values) 
        / df['amount'][:-1].replace(0, np.nan).ffill().bfill().values)
        df = df[self.columns]

        return df

    def d_csv_update(self, code, start='20100101'):
        read_path = f'{self.path}/d_csv'
        csv_path = f'{self.path}/c_csv'
        file_path = os.path.join(read_path, f'{code}_data.csv')
        output_file_path = os.path.join(csv_path, f'{code}_data.csv')

        self.d_csv_api(code, start)
        if os.path.isfile(file_path):
            df = pd.read_csv(file_path)
            df = self.preprocess(df)

            if not os.path.exists(csv_path):
                os.makedirs(csv_path)

            df.to_csv(output_file_path, index=False)
        else:
            self.logger.send_dico(f"d_csv/{code}_data가 없습니다.")

    def market_update(self, code, start='20100101'):
        

    def load_data(self, code, date_from):
        path = os.path.join(f'{self.path}/c_csv', f'{code}_data.csv')
        df = pd.read_csv(path)

        # 날짜 오름차순 정렬
        df = df.sort_values(by='date').reset_index(drop=True)

        # 데이터 전처리
        df = self.preprocess(df)
        df['date'] = df['date'].astype(str)

        # 기간 필터링
        now = datetime.now().strftime("%Y%m%d")
        df['date'] = df['date'].str.replace('-', '')
        df = df[(df['date'] >= date_from) & (df['date'] <= now)]

        df = df.ffill().reset_index(drop=True)

        # 차트 데이터 분리
        chart_data = df['date', 'open', 'high', 'low', 'close', 'volume', 'amount']

        # 학습 데이터 분리
        training_data = None
        training_data = df[self.columns]

        return chart_data, training_data

'''
    def load_data_v3_v4(code, date_from, date_to, ver):
        columns = None

        # 시장 데이터
        df_marketfeatures = pd.read_csv(
            os.path.join(, 'data', ver, 'marketfeatures.csv'), 
            thousands=',', header=0, converters={'date': lambda x: str(x)})

        # 종목 데이터
        df_stockfeatures = None
        for filename in os.listdir(os.path.join(settings.BASE_DIR, 'data', ver)):
            if filename.startswith(code):
                df_stockfeatures = pd.read_csv(
                    os.path.join(settings.BASE_DIR, 'data', ver, filename), 
                    thousands=',', header=0, converters={'date': lambda x: str(x)})
                break

        # 시장 데이터와 종목 데이터 합치기
        df = pd.merge(df_stockfeatures, df_marketfeatures, on='date', how='left', suffixes=('', '_dup'))
        df = df.drop(df.filter(regex='_dup$').columns.tolist(), axis=1)

        # 날짜 오름차순 정렬
        df = df.sort_values(by='date').reset_index(drop=True)

        # 기간 필터링
        df['date'] = df['date'].str.replace('-', '')
        df = df[(df['date'] >= date_from) & (df['date'] <= date_to)]
        df = df.ffill().reset_index(drop=True)


        # 차트 데이터 분리
        chart_data = df[COLUMNS_CHART_DATA]

        # 학습 데이터 분리
        training_data = df[columns].astype(float)
        df.to_csv('df.csv')
        chart_data.to_csv('chart_dat.csv')
        training_data.to_csv('training_data.csv')
        return chart_data, training_data
'''

test = csv_down()
test.market_data('.DJI','N','20100101')
#test.d_csv_down('TSLA')
#test.m_csv_down('SOXL')

