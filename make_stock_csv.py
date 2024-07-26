from koreapi import api, logger
import os
import pandas as pd
from datetime import datetime, timedelta


class csv_down:
    def __init__ (self, path = 'log/csv'):
        self.api = api()
        self.logger = logger()
        self.path = path

    def m_csv_down(self, code, min = '5'):
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

            df = df.drop_duplicates().sort_values(by='datetime').reset_index(drop=True)
            df.to_csv(file_path, index=False)
            return self.logger.send_dico(f"{code} m_csv donwload")

        return self.logger.send_dico(f"{code} m_csv fail")

    def d_csv_down(self, code, start='20100101'):
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
            
        today = datetime.now() +timedelta(days=60)

        while start < today:
            input = start.strftime('%Y%m%d')

            res = pd.DataFrame(self.api.D_STOCK_DATA(code, input))

            res['datetime'] = res['xymd'].astype(int)
            df= res[['datetime','open','high','low','clos','tvol','tamt']]
            if not df_existing.empty:
                df_combined = pd.concat([df_existing, df]).drop_duplicates().reset_index(drop=True)
            else:
                df_combined = df

            df_combined = df_combined.drop_duplicates().sort_values(by=['datetime']).reset_index(drop=True)
            df_combined.to_csv(file_path, index=False)

            start = start + timedelta(days=60)
            df_existing = df_combined
            self.logger.send_dico(f"{code} {start} ~  m_csv donwload")



test = csv_down()
#test.m_csv_down('AAPL')
test.d_csv_down('AAPL')