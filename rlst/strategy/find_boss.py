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
            'return_1m': return_1m,
            'return_3m': return_3m,
            'return_6m': return_6m,
            'return_12m': return_12m,
            'volatility_6m': volatility_6m,
            'mdd_6m': mdd_6m,
        }
        
        fund = self.api.fundamental(code)
        if fund['per'] == 0 or fund['pbr'] == 0:
            return None
        feature_vector.update(fund)
        return feature_vector

    def scale_optics(self, codes: list, features: pd.DataFrame) -> pd.DataFrame:
        #정규화
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)

        #그룹화
        clusterer = OPTICS(min_samples=3) 
        clusterer.fit(scaled_features)

        # 결과 확인
        labels = clusterer.labels_
        print(labels)
        
        averages_by_label = {}
        unique_labels = np.unique(labels)

        for label in unique_labels:
            average_features = features[labels == label].mean(axis=0)
            averages_by_label[label] = average_features

        analysis_df = pd.DataFrame(averages_by_label).transpose().drop(index=-1, errors='ignore')
        
        #그룹 순위 생성
        # A: 모멘텀 강도 (Momentum Strength)
        analysis_df['A_momentum_strength'] =(analysis_df['return_1m'] * 0.3)+ (analysis_df['return_3m'] * 0.3) + (analysis_df['return_6m'] * 0.3)

        # B: 모멘텀 안정성 (Momentum Stability) - 변동성이 0에 가까운 경우를 대비해 작은 값(epsilon)을 더함
        epsilon = 1e-6 
        analysis_df['B_momentum_stability'] = 1 / (analysis_df['volatility_6m'] + epsilon)

        # C: 리스크 관리 (Risk Management) - MDD가 0인 경우를 대비
        analysis_df['C_risk_management'] = 1 / (abs(analysis_df['mdd_6m']) + epsilon)

        # --- 2단계: 각 지표별 순위(Rank) 부여 ---
        # 값이 높을수록 좋은 지표이므로, rank의 ascending=False 옵션을 사용 (높은 값이 1등)
        analysis_df['rank_A'] = analysis_df['A_momentum_strength'].rank(ascending=False)
        analysis_df['rank_B'] = analysis_df['B_momentum_stability'].rank(ascending=False)
        analysis_df['rank_C'] = analysis_df['C_risk_management'].rank(ascending=False)

        # --- 3단계: 최종 스코어 계산 ---
        weights = {'A': 0.5, 'B': 0.3, 'C': 0.2}
        analysis_df['final_score'] = (analysis_df['rank_A'] * weights['A']) +(analysis_df['rank_B'] * weights['B']) + (analysis_df['rank_C'] * weights['C'])

        # --- 4단계: 최종 스코어 기준으로 정렬 ---
        # 점수가 낮을수록 좋은 그룹이므로, 오름차순(ascending=True)으로 정렬
        ranked_groups = analysis_df.sort_values(by='final_score', ascending=True)
        ranked_list = ranked_groups.iloc[:3].index.to_list()

        group_1 = [ticker for ticker, index in zip(codes, labels) if index == ranked_list[0]]
        group_2 = [ticker for ticker, index in zip(codes, labels) if index == ranked_list[1]]
        group_3 = [ticker for ticker, index in zip(codes, labels) if index == ranked_list[2]]
        
        print(ranked_groups)
        print(codes)
        print(group_1)
        print(group_2)
        print(group_3)

        return ranked_groups
    


    def generate_signals(self,candidate_list, data: pd.DataFrame) -> dict:

        return 0
    


    