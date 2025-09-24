# /pages/12_🤖_AI_Assistant.py

import streamlit as st
import pandas as pd
import requests
from openai import OpenAI
import os

# --- 页面设置 ---
st.set_page_config(
    page_title="AI 智能分析助手",
    page_icon="🤖",
    layout="wide"
)

# --- 导入并应用背景样式 ---
from utils import style

style.set_page_background('assets/backgroud.png')

# --- 后端服务配置 ---
# 主 Agent 服务地址，用于文件处理
AGENT_BASE_URL = "http://127.0.0.1:8000"  # 使用 127.0.0.1 而不是 0.0.0.0
FILE_ANALYSIS_ENDPOINT = f"{AGENT_BASE_URL}/analyze_reviews/"

# vLLM OpenAI 风格 API 地址，用于对话
VLLM_BASE_URL = "http://hpc.wisesoe.com:58001/v1"
VLLM_MODEL_NAME = "deepseek-r1-distill-qwen-vllm"


# --- 与后端 AI Agent 交互的函数 ---

def analyze_file_with_agent(uploaded_file):
    """
    通过 HTTP 请求将文件发送到主 Agent 服务进行处理。
    期望后端返回一个 JSON，包含处理后的数据和分析建议。
    """
    try:
        files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(FILE_ANALYSIS_ENDPOINT, files=files, timeout=300)  # 设置较长的超时

        if response.status_code == 200:
            result = response.json()
            # 假设后端返回格式为: {"structured_data": [...], "suggestions": "..."}
            processed_df = pd.DataFrame(result.get("structured_data"))
            suggestions_text = result.get("suggestions")
            return processed_df, suggestions_text
        else:
            error_message = f"文件分析失败。服务器返回状态码: {response.status_code}。错误信息: {response.text}"
            return None, error_message
    except requests.exceptions.RequestException as e:
        error_message = f"无法连接到分析服务，请确认AI Agent主服务正在 {AGENT_BASE_URL} 运行。错误详情: {e}"
        return None, error_message


# --- 与 vLLM 服务交互的函数 ---

# 初始化 OpenAI 客户端，指向您的 vLLM 服务
try:
    client = OpenAI(
        base_url=VLLM_BASE_URL,
        api_key="not-needed"  # 对于本地或私有部署的服务，API密钥通常不是必需的
    )
except Exception as e:
    st.error(f"初始化OpenAI客户端失败: {e}")
    client = None


def get_chat_response(messages):
    """
    使用 OpenAI 客户端与您的 vLLM 模型进行对话。
    """
    if not client:
        return "错误：无法与AI对话服务建立连接。"
    try:
        response = client.chat.completions.create(
            model=VLLM_MODEL_NAME,
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"与AI对话时发生错误: {e}")
        return "抱歉，我在回答时遇到了一个问题。"


# --- Streamlit 页面 UI ---

st.title("🤖 智能舆情分析助手")
st.markdown(
    "上传您的原始评论文件（CSV或Excel），AI将调用BERT模型进行结构化处理，并由大语言模型生成深度分析报告。随后，您可就报告内容与AI进行对话。")
st.markdown("---")

# --- 初始化 Session State ---
if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = None
if "structured_data" not in st.session_state:
    st.session_state.structured_data = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "file_processed" not in st.session_state:
    st.session_state.file_processed = False

# --- 1. 文件上传与分析 ---
with st.container(border=True):
    st.subheader("第一步：上传文件并启动分析")
    uploaded_file = st.file_uploader(
        "支持CSV或Excel格式的评论文件",
        type=['csv', 'xlsx']
    )

    if uploaded_file is not None:
        if st.button("🚀 开始智能分析", type="primary", use_container_width=True):
            with st.spinner("请稍候... AI Agent正在调用BERT模型进行深度分析..."):
                df, report = analyze_file_with_agent(uploaded_file)

            if df is not None:
                st.success("文件分析完成！")
                st.session_state.structured_data = df
                st.session_state.analysis_report = report
                st.session_state.file_processed = True
                # 清空旧的对话历史并添加新的系统提示
                st.session_state.chat_messages = [
                    {"role": "assistant",
                     "content": "您好！我已经分析完您上传的文件。请查看下方的报告和数据，然后我们可以开始对话。"}
                ]
            else:
                st.error(report)  # 如果失败，report变量会包含错误信息
                st.session_state.file_processed = False

# --- 2. 分析结果展示与对话 ---
if st.session_state.file_processed:
    st.markdown("---")
    st.subheader("第二步：查看分析报告并开始对话")

    # 展示分析报告和结构化数据
    with st.expander("点击查看AI生成的分析报告", expanded=True):
        st.markdown(st.session_state.analysis_report)

    with st.expander("点击查看结构化数据详情"):
        st.dataframe(st.session_state.structured_data, use_container_width=True)

    # 对话界面
    st.markdown("#### 与AI对话")

    # 显示历史消息
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 接收用户输入
    if prompt := st.chat_input("就分析报告提问，获取更深入的见解..."):
        # 将用户消息添加到历史记录
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 准备发送给 vLLM 的消息列表，包含系统级上下文
        messages_for_vllm = [
                                {
                                    "role": "system",
                                    "content": f"你是一个专业的景区舆情分析师。你已经分析了一份评论数据，并生成了以下的分析报告：\n\n---报告开始---\n{st.session_state.analysis_report}\n---报告结束---\n\n现在，请根据这份报告和你的专业知识，回答用户的问题。"
                                }
                            ] + st.session_state.chat_messages

        # 获取 AI 的响应
        with st.chat_message("assistant"):
            with st.spinner("AI 正在思考..."):
                response = get_chat_response(messages_for_vllm)
                st.markdown(response)

        # 将 AI 的响应也添加到历史记录
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
else:
    st.info("请先上传文件并完成分析，以便启用对话功能。")