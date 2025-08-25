from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    """추상 클래스"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> dict:
        """
        주어진 데이터를 바탕으로 투자 비중을 결정하는 핵심 로직.
        - data: 종목별 특징 벡터가 포함된 DataFrame
        - returns: {'AAPL': {'type' : 'sell', 'qty': 0, 'avg_price': 230}}} 형태의 딕셔너리
        """
        pass

    def run(self, data: pd.DataFrame) -> dict:
        """전략을 실행하고 결과를 반환하는 공통 메소드"""
        print(f"--- {self.name} 전략 실행 ---")
        weights = self.generate_signals(data)
        print(f"--- 최종 포트폴리오 ---")
        print(weights)
        return weights