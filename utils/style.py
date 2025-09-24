import streamlit as st
import base64


def set_page_background(image_file):
    """
    注入自定义CSS来设置页面背景和统一的纯白色文本。
    """
    try:
        with open(image_file, "rb") as f:
            img_data = f.read()

        b64_encoded = base64.b64encode(img_data).decode()

        css_style = f"""
        <style>
        /* --- 页面背景设置 --- */
        .stApp {{
            background-image: 
                linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.65)), 
                url(data:image/png;base64,{b64_encoded});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* --- 全局文本颜色统一设置为白色 --- */

        /* 标题 (st.title, st.subheader) */
        .stApp h1, .stApp h2, .stApp h3 {{
            color: #FFFFFF; /* <--- 修改为白色 */
        }}

        /* 普通文本 (st.write, st.markdown) */
        .stApp, .stApp .stMarkdown {{
            color: #FFFFFF; /* <--- 修改为白色 */
        }}

        /* 指标卡 (st.metric) */
        .stApp .stMetric-label {{
            color: #FFFFFF; /* <--- 核心修改：指标标签改为白色 */
        }}
        .stApp .stMetric-value {{
            color: #FFFFFF; /* 指标数值保持白色 */
        }}

        /* 小部件的标签 */
        .st-emotion-cache-1629p8f e1nzilvr5, .st-emotion-cache-1qg05j4 e1nzilvr5 {{
            color: #FFFFFF; /* <--- 修改为白色 */
        }}
        
        /* 修改 st.metric 的 value 颜色为白色 */
        div[data-testid="stMetric"] div {{
            color: white !important;
        }}

        /* 如果需要，也可以修改 label 的颜色 */
        div[data-testid="stMetric"] label {{
            color: #E0E0E0 !important; /* 浅灰色，与白色形成对比 */
        }}
        /* 保持一些点缀颜色 */
        .stApp h2, .stApp h3 {{
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 5px;
        }}
        .stApp .stMetric-delta {{
            color: #4CAF50;
        }}

        </style>
        """
        st.markdown(css_style, unsafe_allow_html=True)

    except FileNotFoundError:
        st.warning("背景图片文件未找到，请检查路径。")