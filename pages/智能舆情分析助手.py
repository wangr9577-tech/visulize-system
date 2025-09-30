# /pages/12_🤖_AI_Assistant.py

import streamlit as st
import pandas as pd
from openai import OpenAI
from utils import style
import re
from utils.navigation import create_sidebar_navigation

# --- 页面设置 ---
st.set_page_config(page_title="AI 智能分析与对话", page_icon="🤖", layout="wide")
style.set_page_background('assets/backgroud.png')

create_sidebar_navigation()

# --- [核心修改] API服务地址变为固定常量 ---
# 地址配置不再在UI中显示，简化了界面
AGENT_API_URL = "http://127.0.0.1:8000/v1"
VLLM_URL = "http://hpc.wisesoe.com:58001/v1"

# --- 初始化 Session State ---
# 新增 chat_messages 用于存储对话历史
# 新增 processing_complete 用于控制UI流程
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "suggestions" not in st.session_state:
    st.session_state.suggestions = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "processing_complete" not in st.session_state:
    st.session_state.processing_complete = False

# --- 初始化 API 客户端 ---
try:
    agent_client = OpenAI(base_url=AGENT_API_URL, api_key="not-needed")
    vllm_client = OpenAI(base_url=VLLM_URL, api_key="not-needed")
except Exception as e:
    st.error(f"初始化API客户端失败: {e}")
    agent_client = None
    vllm_client = None


# --- 文本解析与清理函数 ---
def parse_agent_response(text: str) -> dict:
    data = {}
    patterns = {
        "文本摘要": r"文本摘要(?:是|为|：|:)\s*['\"]?(.*?)['\"]?[\n，。]",
        "核心问题类型": r"核心问题类型(?:是|为|：|:)\s*['\"]?(.*?)['\"]?[\n，。]",
        "问题细项": r"问题细项(?:包括|是|为|：|:)\s*['\"]?(.*?)['\"]?[\n，。]",
        "情感强度": r"情感强度(?:是|为|：|:)\s*['\"]?(.*?)['\"]?[\n，。]",
        "是否恶意诋毁": r"是否恶意诋毁(?:是|为|：|:)\s*['\"]?(.*?)['\"]?[\n，。$]"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        data[key] = match.group(1).strip() if match else "N/A"
    if all(v == "N/A" for v in data.values()):
        old_patterns = {
            "文本摘要": r"1\. 文本摘要：(.*?)\n", "核心问题类型": r"2\. 核心问题类型：(.*?)\n",
            "问题细项": r"3\. 问题细项：(.*?)\n",
            "情感强度": r"4\. 情感强度：(.*?)\n", "是否恶意诋毁": r"5\. 是否恶意诋毁：(.*?)$"
        }
        for key, pattern in old_patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            data[key] = match.group(1).strip() if match else "N/A"
    return data


def clean_think_tags(text: str) -> str:
    cleaned_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned_text.strip()


# --- 主界面 UI ---
st.title("🤖 AI 智能分析与对话")
st.markdown("上传评论文件进行分析。分析完成后，您可以在下方与AI对话，深入探讨分析结果。")

# --- 阶段一：文件上传与分析 ---
with st.container(border=True):
    st.subheader("第一步：上传文件并启动分析")
    uploaded_file = st.file_uploader("支持CSV或Excel格式的评论文件", type=['csv', 'xlsx'])

    if uploaded_file and st.button("🚀 开始智能分析", type="primary", use_container_width=True):
        # 重置状态
        st.session_state.analysis_results = None
        st.session_state.suggestions = None
        st.session_state.chat_messages = []
        st.session_state.processing_complete = False

        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            comment_col = '内容' if '内容' in df.columns else 'comment' if 'comment' in df.columns else None
            if not comment_col:
                st.error("上传的文件中未找到名为 '内容' 或 'comment' 的列。")
                st.stop()
            comments = df[comment_col].dropna().tolist()
            if not comments:
                st.warning("文件中没有找到可分析的评论。")
                st.stop()

            # 批量处理
            results_list = []
            progress_bar = st.progress(0, text="开始分析...")
            with st.spinner(f"正在逐条分析 {len(comments)} 条评论..."):
                for i, comment in enumerate(comments):
                    try:
                        response = agent_client.chat.completions.create(model="tourism-sentiment-analyzer",
                                                                        messages=[{"role": "user", "content": comment}])
                        cleaned_text = clean_think_tags(response.choices[0].message.content)
                        parsed_result = parse_agent_response(cleaned_text)
                        parsed_result["原始评论"] = comment
                        results_list.append(parsed_result)
                    except Exception:
                        pass  # 静默处理单条失败
                    progress_bar.progress((i + 1) / len(comments), text=f"已分析 {i + 1}/{len(comments)} 条")
            st.session_state.analysis_results = pd.DataFrame(results_list)
            st.success("所有评论已完成结构化分析！")

            # 生成综合建议
            with st.spinner("AI 正在根据分析结果撰写综合改进建议..."):
                summary_prompt = "你是一位经验丰富的景区运营总监...\n--- 负面评论数据摘要 ---\n"  # (为简洁省略完整Prompt)
                issue_counts = st.session_state.analysis_results['核心问题类型'].value_counts()
                summary_prompt += f"核心问题类型分布统计：\n{issue_counts.to_string()}\n\n"
                top_issues = issue_counts.head(3).index
                summary_prompt += "高频问题类型的评论摘要示例：\n"
                for issue in top_issues:
                    examples = \
                    st.session_state.analysis_results[st.session_state.analysis_results['核心问题类型'] == issue][
                        '文本摘要'].head(2).tolist()
                    summary_prompt += f"- **对于'{issue}'**: {' | '.join(examples)}\n"
                summary_prompt += "\n请开始撰写您的报告。不要包含思考过程或XML标签。"

                suggestion_response = vllm_client.chat.completions.create(model="deepseek-r1-distill-qwen-vllm",
                                                                          messages=[{"role": "user",
                                                                                     "content": summary_prompt}],
                                                                          temperature=0.6, max_tokens=1500)
                st.session_state.suggestions = clean_think_tags(suggestion_response.choices[0].message.content)
                st.success("综合改进建议已生成！")
                st.session_state.processing_complete = True  # 标记处理完成
        except Exception as e:
            st.error(f"处理过程中发生严重错误: {e}")

# --- 阶段二：结果展示与对话 ---
if st.session_state.processing_complete:
    st.markdown("---")
    st.subheader("第二步：查看分析报告并与AI对话")

    # 折叠展示结果，保持界面整洁
    with st.expander("📊 点击查看结构化分析结果详情"):
        st.dataframe(st.session_state.analysis_results, use_container_width=True)

    with st.expander("📝 点击查看AI综合改进建议报告", expanded=True):
        st.markdown(st.session_state.suggestions)

    st.markdown("---")

    # 初始化对话
    if not st.session_state.chat_messages:
        st.session_state.chat_messages.append(
            {"role": "assistant", "content": "分析已完成！现在您可以就这份报告向我提问了。"}
        )

    # 显示历史对话
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 接收用户输入
    if prompt := st.chat_input("就分析报告进行提问..."):
        # 将用户输入添加到历史并显示
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 准备带有上下文的请求
        with st.chat_message("assistant"):
            with st.spinner("AI 思考中..."):
                # 创建一个系统提示，为AI提供上下文
                system_prompt = (
                    "你是一位专业的景区舆情分析师。\n"
                    f"你刚刚为用户生成了一份分析报告，报告内容如下：\n---报告开始---\n{st.session_state.suggestions}\n---报告结束---\n"
                    "现在，请根据这份报告的内容，用简洁、专业的语言回答用户的问题。"
                )

                # 将系统提示和对话历史一起发送
                messages_to_send = [{"role": "system", "content": system_prompt}] + st.session_state.chat_messages

                try:
                    response = vllm_client.chat.completions.create(
                        model="deepseek-r1-distill-qwen-vllm",
                        messages=messages_to_send
                    )
                    cleaned_response = clean_think_tags(response.choices[0].message.content)
                    st.markdown(cleaned_response)
                    # 将AI响应添加到历史
                    st.session_state.chat_messages.append({"role": "assistant", "content": cleaned_response})
                except Exception as e:
                    error_msg = f"与AI对话时发生错误: {e}"
                    st.error(error_msg)