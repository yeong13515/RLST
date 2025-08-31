from rlst.strategy.base_strategy import Strategy
import pandas as pd
import rlst.strategy.find_boss as find_boss
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import OPTICS
import numpy as np

from rlst.core.koreapi import korea_api


class find_boss_stock(Strategy):
    def __init__(self):
        super().__init__(name="최종 모델 v2.0")

        self.vix_threshold = 30
        self.momentum_weights = {'sortino': 0.5, 'return_6m': 0.3, 'return_12m': 0.2}
        self.api = korea_api()

    def preprocessing(self, code: str, features: pd.DataFrame) -> dict:
        """
        하나의 종목 code + pd => vetor 추출
        """
        features['datetime'] = pd.to_datetime(features['datetime'])
        df = features.sort_values(by='datetime').tail(252).copy()
        
        if len(df) < 252:
            return None

        price_latest = df.iloc[-1]['clos']       
        price_1m_ago = df.iloc[-21]['clos']     
        price_3m_ago = df.iloc[-63]['clos']    
        price_6m_ago = df.iloc[-126]['clos']
        price_12m_ago = df.iloc[-252]['clos']  
        
        # 모멘텀
        return_1m = (price_latest / price_1m_ago) - 1 if price_1m_ago > 0 else 0
        return_3m = (price_latest / price_3m_ago) - 1 if price_3m_ago > 0 else 0
        return_6m = (price_latest / price_6m_ago) - 1 if price_6m_ago > 0 else 0
        return_12m = (price_latest / price_12m_ago) - 1 if price_12m_ago > 0 else 0

        df_6m = df.tail(126) 
        
        # 변동성
        daily_returns_6m = df_6m['clos'].pct_change().dropna()
        volatility_6m = daily_returns_6m.std()

        # MDD
        rolling_max_6m = df_6m['clos'].cummax()
        drawdown_6m = (df_6m['clos'] - rolling_max_6m) / rolling_max_6m
        mdd_6m = drawdown_6m.min()

        feature_vector = {
            'code':code,
            'return_1m': return_1m,
            'return_3m': return_3m,
            'return_6m': return_6m,
            'return_12m': return_12m,
            'volatility_6m': volatility_6m,
            'mdd_6m': mdd_6m,
        }

        return feature_vector

    def scale_optics(self, features: pd.DataFrame) -> pd.DataFrame:
        #정규화
        numeric_features = features.select_dtypes(include=np.number)

        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(numeric_features)

        clusterer = OPTICS(min_samples=5) # min_samples는 데이터에 맞게 조정
        clusterer.fit(scaled_features)

        features['cluster'] = clusterer.labels_

        # A: 모멘텀 강도 (Momentum Strength)
        features['rank_A'] =(features['return_1m'] * 0.3)+ (features['return_3m'] * 0.3) + (features['return_6m'] * 0.3)

        # B: 모멘텀 안정성 (Momentum Stability)
        epsilon = 1e-6 
        features['rank_B'] = 1 / (features['volatility_6m'] + epsilon)

        # C: 리스크 관리 (Risk Management) - MDD가 0인 경우를 대비
        features['rank_C'] = 1 / (abs(features['mdd_6m']) + epsilon)

        weights = {'A': 0.5, 'B': 0.3, 'C': 0.2}
        features['final_score'] = (features['rank_A'] * weights['A']) +(features['rank_B'] * weights['B']) + (features['rank_C'] * weights['C'])
        
        features = features.sort_values(by='cluster').sort_values(by='final_score', ascending=True)
        features = features[['code','cluster','final_score']]
        return features


    def code_signals(self, features: pd.DataFrame) -> dict:
        mean_list = features.groupby('cluster')['final_score'].mean().sort_values().index.to_list()
        if -1 in mean_list :
            mean_list.remove(-1)
        
        print(mean_list)
        candidae_dict = {}
        for i in range(len(mean_list)):
            candidae_dict[i] = features[features['cluster'] == mean_list[i]]
            print(candidae_dict[i])
        return candidae_dict
    

    def run(self, fund_dict:dict):
        '''find_boss를 사용하고 싶으면 이거 하나 딸깍으로 만들어야할까?
        리턴은 balance 업데이트 용.
        '''
        total_list = []
        for code in fund_dict:
            #종목 별 features 추출
            pre_temp = self.preprocessing(code, pd.read_csv(f"data/raw/d_csv/{code}_data.csv"))
            pre_fund = fund_dict[code]
            
            if pre_temp != None and pre_fund!= None:
                pre_temp.update(pre_fund)
                total_list.append(pre_temp)

        total_df = self.scale_optics(pd.DataFrame(total_list))
        print(total_df)
        total_candi_dict = self.code_signals(total_df)

        final_candi_list = []

        # 1. 최소 2개의 그룹이 있는지 확인
        if len(total_candi_dict) >= 2:
            group1_df = total_candi_dict[0]
            num_stocks_g1 = len(group1_df)
            top_stocks_g1 = group1_df[:min(num_stocks_g1, 3)]['code'].to_list()
            final_candi_list.extend(top_stocks_g1)

            group2_df = total_candi_dict[1]
            num_stocks_g2 = len(group2_df)
            top_stocks_g2 = group2_df[:min(num_stocks_g2, 2)]['code'].to_list()
            final_candi_list.extend(top_stocks_g2)
            
        else:
            print('후보 미구성')
            return None
        
        weights = {}
        for code in final_candi_list:
            weights[code] = 1/len(final_candi_list)
        print(weights)

        return weights