# /pages/分景区之华山.py

import streamlit as st
from streamlit_echarts import st_pyecharts
from utils import data_loader, style, charts
import numpy as np
from PIL import Image

# --- 页面基本配置 ---
SCENIC_SPOT_NAME = "华山"
BANNER_IMAGE_PATH = "assets/jingqu/huashan.png"
FONT_PATH = "assets/simhei.ttf" # 词云图字体路径

# --- 页面设置 ---
st.set_page_config(
    page_title=f"{SCENIC_SPOT_NAME} | 舆情分析",
    page_icon="⛰️",
    layout="wide"
)

# --- 加载数据和应用样式 ---
style.set_page_background('assets/backgroud.png')
df_full = data_loader.load_data('data/sentiment_data.csv')
# 筛选出当前景区的所有数据，用于静态词云图和筛选器选项
df_scenic_all = df_full[df_full['景区名称'] == SCENIC_SPOT_NAME]


# --- 侧边栏筛选器 ---
st.sidebar.header(f"{SCENIC_SPOT_NAME} 数据筛选")

platforms = df_scenic_all['平台'].unique()
selected_platforms = st.sidebar.multiselect(
    "选择平台:",
    options=platforms,
    default=platforms
)

issue_types = df_scenic_all['核心问题类型'].unique()
selected_issue_types = st.sidebar.multiselect(
    "选择核心问题类型:",
    options=issue_types,
    default=issue_types
)

sentiments = df_scenic_all['情感强度'].unique()
selected_sentiments = st.sidebar.multiselect(
    "选择情感强度:",
    options=sentiments,
    default=sentiments
)

# --- 根据筛选器过滤数据 ---
df_filtered = data_loader.filter_data(
    df_full,
    scenic_spot=SCENIC_SPOT_NAME,
    platforms=selected_platforms,
    issue_types=selected_issue_types,
    sentiment_levels=selected_sentiments
)


# --- 页面主内容 ---

# 1. 标题和横幅
st.markdown(f"<h1 style='text-align: center;'>{SCENIC_SPOT_NAME} 负面舆情分析</h1>", unsafe_allow_html=True)
try:
    st.image(BANNER_IMAGE_PATH)
except Exception:
    st.warning(f"景区图片未找到，请确认路径 {BANNER_IMAGE_PATH} 是否正确。")

st.markdown("---")

# 2. 评论数量
# st.metric(label="筛选后评论总数", value=f"{len(df_filtered)} 条")

# st.markdown("---")


# 3. 图表布局
# 我们将词云图放在上面，占据整行；下面的两个图表并排
# --- 词云图显示部分 (核心修改) ---
st.subheader("评论内容词云图")
mask = np.array(Image.open('assets/ditu/huashanditu.png'))
# 调用新函数获取图片路径
# 注意：我们传入的是完整的数据集 df_full，函数内部会自己筛选
wordcloud_image_path = charts.get_or_create_wordcloud_image(
    df=df_full,
    scenic_name=SCENIC_SPOT_NAME,
    font_path=FONT_PATH,
    mask_image=mask
)

# 使用 st.image 显示保存好的图片

if wordcloud_image_path:
    st.image(wordcloud_image_path, use_container_width=True)
else:
    # 如果函数返回None，则显示提示信息
    st.info("无法为您展示词云图。")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    # 按问题内容的柱状图 (动态)
    if not df_filtered.empty:
        issue_bar_chart = charts.create_scenic_issue_bar(df_filtered)
        if issue_bar_chart:
            st_pyecharts(issue_bar_chart, height="400px")
    else:
        st.info("根据当前筛选条件，无数据显示。")

with col2:
    # 按时间的折线图 (动态)
    if not df_filtered.empty:
        timeline_chart = charts.create_scenic_timeline(df_filtered)
        if timeline_chart:
            st_pyecharts(timeline_chart, height="400px")
    else:
        st.info("根据当前筛选条件，无数据显示。")

st.markdown("---")  # 添加一个分隔线

st.subheader("详细评论数据浏览")

# 为了更好的展示，我们只选择部分核心列
# 您可以根据需要修改这个列表来展示不同的列
columns_to_display = [
    '点评时间',
    '平台',
     '核心问题类型',
    '具体问题',
    '情感强度',
    '内容'  # 如果您有'文本摘要'列并且希望显示更简洁的内容，可以替换'内容'
 ]

 # 过滤掉数据中不存在的列名，避免程序出错
existing_columns_to_display = [col for col in columns_to_display if col in df_filtered.columns]

# 使用 st.dataframe 来展示数据
# use_container_width=True 让表格宽度自适应页面
# hide_index=True 隐藏 DataFrame 默认的行号索引
st.dataframe(
    df_filtered[existing_columns_to_display],
    use_container_width=True,
    hide_index=True
 )