# /pages/home.py

import streamlit as st
from streamlit_echarts import st_pyecharts
from utils import data_loader, style, charts
import streamlit.components.v1 as components
import time
from utils.navigation import create_sidebar_navigation

# --- 页面配置 ---
# Streamlit要求set_page_config必须是第一个命令
st.set_page_config(
    page_title="舆情总览 | 旅游景区负面舆情可视化查询系统",
    page_icon="🗺️",
    layout="wide"
)

create_sidebar_navigation()

# --- 加载数据和设置页面样式 ---
# 应用背景图
style.set_page_background('assets/backgroud.png')
# 加载数据
df = data_loader.load_data('data/sentiment_data.csv')

# --- 页面内容 ---

# 1. 页面标题
st.title("旅游景区负面舆情总览")
st.markdown("---")

# 2. 顶部核心指标
total_reviews, platform_count, scenic_spot_count = data_loader.get_total_metrics(df)
cols_metric = st.columns(3)
with cols_metric[0]:
    st.metric(label="负面舆情总量", value=f"{total_reviews} 条")
with cols_metric[1]:
    st.metric(label="涉及平台总数", value=f"{platform_count} 个")
with cols_metric[2]:
    st.metric(label="涉及景区总数", value=f"{scenic_spot_count} 个")

st.markdown("---")

# 3. 页面主体布局：左、中、右三列
left_col, mid_col, right_col = st.columns([3, 5, 3])

# --- 中间列内容 ---
with mid_col:
    with st.container():
        st.subheader("舆情地理分布热力图")
        map_chart = charts.create_china_heatmap(df)
        # 渲染为 HTML
        chart_html = map_chart.render_embed()
        # 在 Streamlit 中显示
        components.html(chart_html, height=500, width=500, scrolling=False)

    with st.container():
        st.subheader("月度舆情数量趋势图")
        line_chart = charts.create_monthly_reviews_line(df)
        st_pyecharts(line_chart, height="400px")

# --- 左侧列内容 ---
with left_col:
    with st.container():
        st.subheader("各景区舆情数量排行")
        bar_chart = charts.create_scenic_reviews_bar(df)
        # 增加图表高度以容纳所有景区
        st_pyecharts(bar_chart, height="500px", width = '350px')

    with st.container():
        scenic_list = df['景区名称'].unique().tolist()

        radar_chart = charts.create_scenic_quantity_radar(df)
        st_pyecharts(radar_chart, height="400px", width = '300px')

# --- 右侧列内容 ---
with right_col:
    with st.container():
        st.subheader("高频问题细项")
        issue_bar = charts.create_issue_details_horizontal_bar(df)
        st_pyecharts(issue_bar, height="320px")

    with st.container():
        st.subheader("平台与情感强度分布")
        platform_pie = charts.create_platform_pie(df)
        st_pyecharts(platform_pie, width="300px", height="280px")

        sentiment_pie= charts.create_sentiment_pie(df)
        st_pyecharts(sentiment_pie, width="300px", height="280px")
