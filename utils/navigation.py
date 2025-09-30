# /utils/navigation.py

import streamlit as st
import os


def inject_custom_css():
    """注入CSS来隐藏Streamlit的默认多页面导航"""
    st.markdown(
        """
        <style>
            /* 隐藏Streamlit自动生成的多页面导航 */
            [data-testid="stSidebarNavItems"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


def create_sidebar_navigation():
    """创建并显示一个自定义的侧边栏导航组件"""

    # 1. 注入CSS，隐藏默认导航
    inject_custom_css()

    # 2. 定义景区页面
    # 字典的键是显示在下拉框中的名称，值是对应的文件路径
    # 提示：为了让Streamlit正确排序，最好在文件名前加上数字和下划线
    SCENIC_SPOTS = {
        "华山": "pages/分景区之华山.py",
        "峨眉山": "pages/分景区之峨眉山.py",
        "嵩山": "pages/分景区之嵩山.py",
        "庐山": "pages/分景区之庐山.py",
        "恒山": "pages/分景区之恒山.py",
        "普陀山": "pages/分景区之普陀山.py",
        "武夷山": "pages/分景区之武夷山.py",
        "泰山": "pages/分景区之泰山.py",
        "衡山": "pages/分景区之衡山.py",
        "雁荡山": "pages/分景区之雁荡山.py",
        "黄山": "pages/分景区之黄山.py"
        # ... 请根据您的实际文件名补全所有11个景区 ...
    }

    # 3. 显示固定链接
    # 使用 st.page_link，这是Streamlit推荐的导航方式
    st.sidebar.page_link("home.py", label="**舆情总览**", icon="🏠")
    st.sidebar.markdown("---")

    # 4. 创建下拉选择框
    spot_names = list(SCENIC_SPOTS.keys())
    options = ["--- 请选择景区 ---"] + spot_names

    selected_spot = st.sidebar.selectbox(
        "**分景区舆情分析**",
        options,
        label_visibility="collapsed"  # 隐藏默认标签，让标题看起来更像一个整体
    )

    # 5. 根据选择进行页面跳转
    if selected_spot and selected_spot != "--- 请选择景区 ---":
        # 使用 st.switch_page 进行跳转
        page_path = SCENIC_SPOTS[selected_spot]
        st.switch_page(page_path)

    st.sidebar.markdown("---")
    st.sidebar.page_link("pages/智能舆情分析助手.py", label="**智能舆情分析助手**", icon="🤖")