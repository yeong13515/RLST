from koreapi import api, logger
import os
import pandas as pd


class csv_down:
    def __init__ (self, path = 'log/csv'):
        self.api = api()
        self.logger = logger()
        self.path = path

    def m_csv_down(self, code, csv_path = f'{self.path}/m_csv' ):
        file_path = os.path.join(self.csv_path, f'{code}_data.csv')
        if not os.path.exists(self.csv_path):
            os.makedirs(self.csv_path)

        df = pd.DataFrame(self.api.M_STOCK_DATA(code, self.min))
        df = df[['xymd', 'xhms', 'open', 'high', 'low', 'last']]
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['xymd'] + ' ' + df['xhms'], format='%Y%m%d %H%M%S')
            df.drop(columns=['xymd', 'xhms'], inplace=True)
            df = df[['datetime','open', 'high','low','last']]
            if os.path.isfile(self.file_path):
                df_existing = pd.read_csv(self.file_path)
                df_existing['datetime'] = pd.to_datetime(df_existing['datetime'])
                df = pd.concat([df_existing, df])

            df = df.drop_duplicates().sort_values(by='datetime').reset_index(drop=True)
            df.to_csv(self.file_path, index=False)
            self.logger.send_dico(f"{code} 가져오기 완료 m_csv")

        return self.logger.send_dico(f"{code} 가져오기 오류 m_csv")

    def d_csv_down(self, code, csv_path = f'{self.path}/m_csv', start='20100101'):
        file_path = os.path.join(csv_path, f'{code}_data.csv')
        if not os.path.exists(self.csv_path):
            os.makedirs(self.csv_path)
        
        if os.path.isfile(self.file_path):
            df_existing = pd.read_csv(self.file_path)
            latest_date = pd.to_datetime(df_existing['date']).max()
            start = latest_date.strftime('%Y%m%d')
        else:
            df_existing = pd.DataFrame()
            if start is None:
                start = self.start

        res = self.api.D_STOCK_DATA(self.code, start)
        res['date'] = pd.to_datetime(res['date'], format='%Y%m%d')
        df = pd.dataFrame(res)

        if not df_existing.empty:
            df_combined = pd.concat([df_existing, df]).drop_duplicates().reset_index(drop=True)
        else:
            df_combined = df

        df_combined = df_combined.drop_duplicates().sort_values(by=['date', 'time']).reset_index(drop=True)

        df_combined.to_csv(self.file_path, index=False)

test = csv_down()
test.m_csv_down('AAPL')
test.d_csv_down('AAPL')