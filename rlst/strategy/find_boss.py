from rlst.strategy.base_strategy import Strategy
import pandas as pd
import rlst.strategy.find_boss as find_boss
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import OPTICS


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
            'return_1m': return_1m,
            'return_3m': return_3m,
            'return_6m': return_6m,
            'return_12m': return_12m,
            'volatility_6m': volatility_6m,
            'mdd_6m': mdd_6m,
        }

        feature_vector.update(self.api.fundamental(code))

        return feature_vector

    def scale_optics(self, codes: list, features: pd.DataFrame) -> pd.DataFrame:
        test_df = pd.read_csv('data/raw/d_csv/AAPL_data.csv')
        pre_aapl = self.preprocessing('AAPL',test_df)

        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)
        print("클러스터링에 입력되는 데이터 크기:", scaled_features.shape)

        print(scaled_features)
        clusterer = OPTICS(min_samples=3) 
        clusterer.fit(scaled_features)

        # 결과 확인
        labels = clusterer.labels_
        print(labels)
        
        for i, code in enumerate(codes):
            
        return 0

    def generate_signals(self, candidate_list, d_m, data):
        

        return 0
    
    


    