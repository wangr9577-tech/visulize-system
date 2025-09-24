# /utils/charts.py
from pyecharts import options as opts
from pyecharts.charts import Map, Bar, Radar, Line, Pie, Funnel
from pyecharts.globals import ThemeType
import streamlit.components.v1 as components
import pandas as pd
import streamlit as st
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os

# --- 主题和颜色配置 ---
CHART_THEME = ThemeType.DARK
TEXT_COLOR = "#FFFFFF"
ACCENT_COLOR = "#4CAF50"

china_provinces = [
    "北京市","天津市","上海市","重庆市","河北省","山西省","辽宁省","吉林省","黑龙江省",
    "江苏省","浙江省","安徽省","福建省","江西省","山东省","河南省","湖北省","湖南省",
    "广东省","海南省","四川省","贵州省","云南省","陕西省","甘肃省","青海省",
    "台湾省","内蒙古自治区","广西壮族自治区","西藏自治区","宁夏自治区","新疆维吾尔自治区","香港特别行政区","澳门特别行政区"
]

def create_china_heatmap(df: pd.DataFrame):
    """根据各景区的舆情数生成中国地图热力图"""
    province_reviews = df.groupby('省份').size().reindex(china_provinces, fill_value=0).reset_index()
    province_reviews .columns = ["省份", "舆情数"]
    data_pairs = list(zip(province_reviews['省份'], province_reviews['舆情数']))

    map_chart = (
        Map(init_opts=opts.InitOpts(
            theme=CHART_THEME,
            bg_color="transparent",
            width="500px",  # 设置宽度
            height="600px"  # 设置高度
        ))
        .add(
            series_name="负面舆情数量",
            data_pair=data_pairs,
            maptype="china",
            is_map_symbol_show=False,
            label_opts=opts.LabelOpts(is_show=False)  # 去掉省份名称
        )
        .set_global_opts(
            visualmap_opts=opts.VisualMapOpts(
                min_=0,
                max_=2500,
                is_piecewise=False,
                range_color=["#D3D3D3", "#FFFF00", "#8B0000"],  # 浅灰 → 黄 → 深红
                pos_left="5%",
                pos_top="center"
            ),
            tooltip_opts=opts.TooltipOpts(
                formatter="{b}: {c}"
            )
        )
    )
    return map_chart


def create_scenic_reviews_bar(df: pd.DataFrame):
    """创建各景区舆情数柱状图"""
    scenic_counts = df['景区名称'].value_counts().sort_values(ascending=True)

    bar_chart = (
        Bar(init_opts=opts.InitOpts(theme=CHART_THEME, bg_color="transparent"))
        .add_xaxis(scenic_counts.index.tolist())
        .add_yaxis("舆情数", scenic_counts.values.tolist(), label_opts=opts.LabelOpts(is_show=False))
        .reversal_axis()  # 转换为水平条形图
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title_textstyle_opts=opts.TextStyleOpts(color=TEXT_COLOR)
            ),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(color=TEXT_COLOR),
                name_textstyle_opts=opts.TextStyleOpts(color=TEXT_COLOR)
            ),
            yaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(color=TEXT_COLOR, font_size=8),
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
            datazoom_opts=[
                opts.DataZoomOpts(
                    type_="inside",
                    orient="vertical",
                )
            ],
        )
        .set_series_opts(
            itemstyle_opts=opts.ItemStyleOpts(color=ACCENT_COLOR)
        )
    )
    return bar_chart


def create_scenic_quantity_radar(df: pd.DataFrame):
    """
    创建一个新的雷达图，维度为所有景区，展现各景区的舆情数量。
    """
    # 1. 计算每个景区的舆情数
    scenic_counts = df['景区名称'].value_counts()

    # 2. 创建雷达图的 schema (维度)
    # 每个维度是一个字典，包含名称和该维度的最大值
    max_count = int(scenic_counts.max())
    schema = [
        opts.RadarIndicatorItem(name=scenic, max_=max_count)
        for scenic in scenic_counts.index
    ]

    # 3. 准备雷达图的数据
    # 只有一组数据，名称为"舆情数量"
    radar_data = [
        opts.RadarItem(
            name="舆情数量",
            value=scenic_counts.values.tolist()
        )
    ]

    # 4. 生成图表
    radar_chart = (
        Radar(init_opts=opts.InitOpts(theme=CHART_THEME, bg_color="transparent"))
        .add_schema(
            schema=schema,
            shape="circle",
            center=["50%", "50%"],
            radius="80%",
            splitarea_opt=opts.SplitAreaOpts(
                is_show=True,
                areastyle_opts=opts.AreaStyleOpts(opacity=1)
            ),
            axisline_opt=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(color=TEXT_COLOR, opacity=0.3)
            ),
            # 添加维度标签样式配置
            textstyle_opts=opts.TextStyleOpts(
                color=TEXT_COLOR,
                font_size=6  # 调整维度标签字体大小
            )
        )
        .add(
            series_name="舆情数量",
            data=radar_data,
            areastyle_opts=opts.AreaStyleOpts(opacity=0.4, color=ACCENT_COLOR),
            linestyle_opts=opts.LineStyleOpts(color=ACCENT_COLOR)
        )
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title_textstyle_opts=opts.TextStyleOpts(color=TEXT_COLOR)
            ),
            legend_opts=opts.LegendOpts(
                textstyle_opts=opts.TextStyleOpts(color=TEXT_COLOR),
                pos_top="5%"
            ),
            tooltip_opts=opts.TooltipOpts(trigger="item"),
        )
    )
    return radar_chart
def create_monthly_reviews_line(df: pd.DataFrame):
    """创建月度舆情数量折线图"""
    monthly_counts = df['月份'].value_counts().sort_index()

    line_chart = (
        Line(init_opts=opts.InitOpts(theme=CHART_THEME, bg_color="transparent"))
        .add_xaxis([f"{m}月" for m in monthly_counts.index])
        .add_yaxis(
            "舆情数",
            monthly_counts.values.tolist(),
            is_smooth=True,
            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max"), opts.MarkPointItem(type_="min")]),
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="月度舆情趋势",
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(color=TEXT_COLOR)
            ),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color=TEXT_COLOR)),
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color=TEXT_COLOR)),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
        )
        .set_series_opts(
            linestyle_opts=opts.LineStyleOpts(width=3, color=ACCENT_COLOR),
            itemstyle_opts=opts.ItemStyleOpts(color=ACCENT_COLOR)
        )
    )
    return line_chart


def create_issue_details_horizontal_bar(df: pd.DataFrame):
    """创建问题细项水平条形图"""
    detail_counts = df['问题细项'].value_counts().sort_values(ascending=False).head(10)

    bar_chart = (
        Bar(init_opts=opts.InitOpts(theme=CHART_THEME, bg_color="transparent"))
        .add_xaxis(detail_counts.index.tolist())
        .add_yaxis("数量", detail_counts.values.tolist())
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="TOP 10 问题细项",
                title_textstyle_opts=opts.TextStyleOpts(color=TEXT_COLOR)
            ),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=60, color=TEXT_COLOR, font_size=8)
            ),
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color=TEXT_COLOR)),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
        )
    )
    return bar_chart


def create_platform_pie(df: pd.DataFrame):
    """创建平台来源饼图"""
    platform_counts = df['平台'].value_counts()
    data_pair = [[platform, count] for platform, count in platform_counts.items()]

    pie_chart = (
        Pie(init_opts=opts.InitOpts(theme=CHART_THEME, bg_color="transparent", width="300px", height="300px"))
        .add(
            series_name="平台来源",
            data_pair=data_pair,
            radius=["40%", "70%"],
            label_opts=opts.LabelOpts(
                position="inside",
                formatter="{b}: {c} ({d}%)",
            )
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(color=TEXT_COLOR)
            ),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    return pie_chart


def create_sentiment_pie(df: pd.DataFrame):
    """创建情感强度饼图"""
    sentiment_counts = df['情感强度'].value_counts()
    data_pair = [[sentiment, count] for sentiment, count in sentiment_counts.items()]
    pie_chart = (
        Pie(init_opts=opts.InitOpts(theme=CHART_THEME, bg_color="transparent", width="300px", height="300px"))
        .add(
            series_name="情感强度",
            data_pair=data_pair,
            radius=["40%", "70%"],
            label_opts=opts.LabelOpts(
                position="inside",
                formatter="{b}: {d}%",
            )
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                pos_left="center",
            ),
            legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%"),
        )
    )
    return pie_chart


import pandas as pd
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
import streamlit as st
import numpy as np
from PIL import Image


def create_scenic_issue_bar(df: pd.DataFrame):
    """为特定景区创建按问题内容的柱状图"""
    issue_counts = df['核心问题类型'].value_counts()

    bar_chart = (
        Bar(init_opts=opts.InitOpts(theme=CHART_THEME, bg_color="transparent"))
        .add_xaxis(issue_counts.index.tolist())
        .add_yaxis("数量", issue_counts.values.tolist(), color=ACCENT_COLOR)
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="核心问题类型分布",
                title_textstyle_opts=opts.TextStyleOpts(color=TEXT_COLOR)
            ),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=15, color=TEXT_COLOR)
            ),
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color=TEXT_COLOR)),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
        )
    )
    return bar_chart


def create_scenic_timeline(df: pd.DataFrame):
    """为特定景区创建按时间的折线图"""
    # 确保'月份'列存在
    if '月份' not in df.columns:
        return None

    monthly_counts = df['月份'].value_counts().sort_index()

    line_chart = (
        Line(init_opts=opts.InitOpts(theme=CHART_THEME, bg_color="transparent"))
        .add_xaxis([f"{m}月" for m in monthly_counts.index])
        .add_yaxis(
            "舆情数",
            monthly_counts.values.tolist(),
            is_smooth=True,
            linestyle_opts=opts.LineStyleOpts(width=3, color=ACCENT_COLOR),
            itemstyle_opts=opts.ItemStyleOpts(color=ACCENT_COLOR)
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="评论时间趋势",
                title_textstyle_opts=opts.TextStyleOpts(color=TEXT_COLOR)
            ),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color=TEXT_COLOR)),
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color=TEXT_COLOR)),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
        )
    )
    return line_chart


def get_or_create_wordcloud_image(df: pd.DataFrame, scenic_name: str, font_path='assets/simhei.ttf',
                                  output_dir='assets/wordclouds', mask_image=None):
    """
    检查词云图图片是否存在。如果不存在，则生成并保存；然后返回图片路径。

    Args:
        df (pd.DataFrame): 包含所有数据的完整DataFrame。
        scenic_name (str): 当前景区的名称，用于命名文件和筛选数据。
        font_path (str): 字体文件路径。
        output_dir (str): 保存生成图片的目录。

    Returns:
        str: 生成的词云图图片的路径，如果失败则返回 None。
    """
    # 1. 定义输出路径并确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    image_path = os.path.join(output_dir, f"{scenic_name}.png")

    # 2. 检查图片是否已存在，如果存在则直接返回路径
    if os.path.exists(image_path):
        return image_path

    # 筛选当前景区数据并准备文本
    df_scenic = df[df['景区名称'] == scenic_name]
    if '内容' not in df_scenic.columns or df_scenic['内容'].dropna().empty:
        st.warning(f"“{scenic_name}”没有评论内容，无法生成词云图。")
        return None

    text = " ".join(review for review in df_scenic['内容'].astype(str).dropna())
    if not text.strip():
        return None

    # 分词
    word_list = jieba.cut(text, cut_all=False)
    words = " ".join(word_list)

    with open('assets/hit_stopwords.txt', 'r', encoding='utf-8') as f:
        stopwords = f.read().splitlines()

    # 创建词云图对象
    wc = WordCloud(
        font_path=font_path,
        background_color="rgba(255, 255, 255, 0)",
        mode="RGB",
        width=800,
        height=500,
        max_words=150,
        stopwords=stopwords,  # 停用词
        mask=mask_image,  # 形状掩码
        colormap='viridis',
        contour_width = 1,  # 轮廓宽度
        contour_color = 'steelblue',  # 轮廓颜色
        collocations = False,  # 不考虑词语搭配
        prefer_horizontal = 0.7,  # 水平词语比例
        scale = 2,  # 缩放比例以提高清晰度
        min_font_size = 10,  # 最小字体大小
        max_font_size = 200,  # 最大字体大小
        random_state = 42  # 随机种子以确保可重复性
    )

    # 生成词云
    wc.generate(words)

    # 使用 matplotlib 绘制并保存
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')

    try:
        # 保存图像，bbox_inches='tight' 和 pad_inches=0 可以去除白边
        # transparent=True 使背景透明
        fig.savefig(image_path, format='png', transparent=True, bbox_inches='tight', pad_inches=0)
        plt.close(fig)  # 关闭图像，释放内存
        return image_path
    except Exception as e:
        st.error(f"保存词云图失败: {e}")
        plt.close(fig)
        return None