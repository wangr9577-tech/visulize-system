# /utils/data_loader.py

import pandas as pd
import streamlit as st
import numpy as np
import os

# 定义景区和对应省份的映射
SCENIC_PROVINCE_MAP = {
    '普陀山': '浙江省', '黄山': '安徽省', '庐山': '江西省', '雁荡山': '浙江省',
    '泰山': '山东省', '衡山': '湖南省', '华山': '陕西省', '恒山': '山西省',
    '嵩山': '河南省', '峨眉山': '四川省', '武夷山': '福建省'
}
@st.cache_data
def load_data(file_path='data/sentiment_data.csv'):
    """
    加载并预处理数据。
    如果真实数据文件不存在，则加载模拟数据。
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='gbk')

    # 对真实数据进行预处理
    df['点评时间'] = pd.to_datetime(df['点评时间'], errors='coerce')
    df.dropna(subset=['点评时间'], inplace=True)
    df['月份'] = df['点评时间'].dt.month
    df['省份'] = df['景区名称'].map(SCENIC_PROVINCE_MAP)

    return df
def get_total_metrics(df):
    """ 计算舆情总量、平台数、景区数 """
    total_reviews = len(df)
    platform_count = df['平台'].nunique()
    scenic_spot_count = df['景区名称'].nunique()
    return total_reviews, platform_count, scenic_spot_count


def filter_data(df, scenic_spot, platforms, issue_types, sentiment_levels):
    """
    根据筛选器条件过滤特定景区页面的数据。
    """
    # 1. 首先筛选出特定景区的数据
    filtered_df = df[df['景区名称'] == scenic_spot].copy()

    # 2. 根据传入的筛选条件进行进一步过滤
    if platforms:
        filtered_df = filtered_df[filtered_df['平台'].isin(platforms)]
    if issue_types:
        filtered_df = filtered_df[filtered_df['核心问题类型'].isin(issue_types)]
    if sentiment_levels:
        filtered_df = filtered_df[filtered_df['情感强度'].isin(sentiment_levels)]

    return filtered_df