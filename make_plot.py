import koreapi
import datetime
import plotly.express as px
import plotly.io as pio
import csv

# 예제 데이터와 플롯 생성
df = px.data.iris()
fig = px.scatter(df, x='sepal_width', y='sepal_length', color='species')

# HTML로 변환
pio.write_html(fig, file='plot.html', auto_open=True)

