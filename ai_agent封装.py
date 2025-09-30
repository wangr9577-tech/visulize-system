
import os

# 关闭TensorFlow的oneDNN警告
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import torch
import joblib
import warnings
import re
from transformers import BertTokenizer, BertModel
from langchain.tools import BaseTool
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from typing import Optional, List, Dict, Any, ClassVar

# 过滤所有警告
warnings.filterwarnings("ignore")


# 1. BERT 舆情模型
class BertTourismModel:
    def __init__(self, model_path, encoder_path, bert_pretrain_path, max_len=256):
        self.DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.MAX_LEN = max_len
        self.bert_pretrain_path = bert_pretrain_path

        encoders = joblib.load(encoder_path)
        self.core_encoder = encoders["core_encoder"]
        self.senti_encoder = encoders["senti_encoder"]
        self.mali_encoder = encoders["mali_encoder"]

        self.tokenizer = BertTokenizer.from_pretrained(bert_pretrain_path)
        self.model = self._build_multi_task_model(model_path)
        self.model.eval()
        print(f"✅ BERT舆情模型加载成功（设备：{self.DEVICE}）")

    def _build_multi_task_model(self, model_path):
        class BertMultiTaskModel(torch.nn.Module):
            def __init__(self, bert_name, num_core, num_senti, num_mali):
                super().__init__()
                self.bert = BertModel.from_pretrained(bert_name)
                hidden_dim = self.bert.config.hidden_size
                self.core_classifier = torch.nn.Linear(hidden_dim, num_core)
                self.senti_classifier = torch.nn.Linear(hidden_dim, num_senti)
                self.mali_classifier = torch.nn.Linear(hidden_dim, num_mali)

            def forward(self, input_ids, attention_mask):
                cls_emb = self.bert(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state[:, 0, :]
                return (self.core_classifier(cls_emb),
                        self.senti_classifier(cls_emb),
                        self.mali_classifier(cls_emb))

        num_core = len(self.core_encoder.classes_)
        num_senti = len(self.senti_encoder.classes_)
        num_mali = len(self.mali_encoder.classes_)

        model = BertMultiTaskModel(
            bert_name=self.bert_pretrain_path,
            num_core=num_core, num_senti=num_senti, num_mali=num_mali
        ).to(self.DEVICE)

        # 过滤不存在的detail_classifier参数
        state_dict = torch.load(model_path, map_location=self.DEVICE)
        filtered_state_dict = {k: v for k, v in state_dict.items() if "detail_classifier" not in k}
        model.load_state_dict(filtered_state_dict, strict=False)

        return model

    def predict(self, text):
        encoding = self.tokenizer(
            text, max_length=self.MAX_LEN, padding="max_length", truncation=True, return_tensors="pt"
        ).to(self.DEVICE)

        with torch.no_grad():
            core_logits, senti_logits, mali_logits = self.model(
                encoding["input_ids"], encoding["attention_mask"]
            )

        core_pred = self.core_encoder.inverse_transform(torch.argmax(core_logits, dim=1).cpu().numpy())[0]
        senti_pred = self.senti_encoder.inverse_transform(torch.argmax(senti_logits, dim=1).cpu().numpy())[0]
        mali_pred = self.mali_encoder.inverse_transform(torch.argmax(mali_logits, dim=1).cpu().numpy())[0]

        if str(mali_pred).lower() in ["是", "true"]:
            core_pred = "无（属于恶意诋毁）"

        return {
            "输入文本": text[:50] + "..." if len(text) > 50 else text,
            "核心问题类型": core_pred,
            "情感强度": senti_pred,
            "是否恶意诋毁": "是" if str(mali_pred).lower() in ["是", "true"] else "否"
        }


# 2. Tool 封装
class TourismBertTool(BaseTool):
    name: str = "tourism_bert_analyzer"
    description: str = "分析旅游舆情的唯一工具。输入：旅游评论/投诉（如'景区门票贵'）；输出：文本摘要、核心问题、细项、情感、是否恶意。仅适用于含有负面情绪的文本。"
    bert_model: BertTourismModel
    llm: ChatOpenAI

    core_mappings: ClassVar[Dict[str, str]] = {
        r'强制|强推|捆绑|强卖|霸王条款': '强制消费问题',
        r'消费|价格|定价|收费|物价|费用|票价|餐价': '消费价格问题',
        r'排队|拥挤|等待|人流|客流|超载|承载': '流量问题',
        r'态度|服务|客服|导游服务|工作人员|推卸|推诿': '服务态度问题',
        r'售后|投诉|退货|退款|退订|退改': '售后问题',
        r'票务|门票|购票|退票|验票|套餐|黄牛': '票务问题',
        r'设施|维护|设备|厕所|停车|缆车|观光车|索道|步道': '设施问题',
        r'引导|指示|导视|导航|指引|标识|路标': '引导问题',
        r'卫生|环境|垃圾': '卫生问题',
        r'安全|隐患|防护|救援|安保|治安|应急': '安全问题',
        r'交通|司机|车辆|黑车|接驳|拥堵|公交车|出租车|摆渡车': '交通问题',
        r'管理|秩序|调度|管控|限流|效率|安检|安排|规则': '管理问题',
        r'体验|游玩|观景|住宿体验|景色|景点|风景|景观|活动': '体验问题',
        r'餐饮|食物|菜品|餐品|餐食|饮品': '餐饮问题',
        r'住宿|酒店|民宿|客房': '住宿问题',
        r'导游|导购|讲解': '导游服务问题',
        r'性价比|价值': '性价比问题',
        r'欺诈|欺骗|虚假|宰客|拉客': '消费欺诈问题',
        r'宣传|不实|名不副实|广告': '宣传问题',
        r'信息|通知|政策|告知': '信息传达问题',
        r'商业化|商业味|推销': '过度商业化问题',
        r'商品|商家|供应商|商贩|店铺|产品': '商品商店相关问题',
        r'平台|旅行社': '平台旅行社相关问题',
        r'系统|APP|网络|故障|订单|技术|支付': '技术故障问题'
    }

    def _generate_summary(self, text: str, is_malicious: bool) -> str:
        if is_malicious:
            return "无（文本属于恶意诋毁，无需提取有效信息）"

        prompt = f"""
         直接返回以下旅游评论的核心问题摘要：
        - 仅保留与不满相关的关键细节
        - 50字以内，纯客观描述
        - 不要包含任何思考过程
        - 直接输出摘要文本

        评论：{text}
        """
        response = self.llm.invoke(prompt)
        summary = response.content.strip()

        # 清除think标记和多余内容
        summary = re.sub(r'<think>.*?</think>', '', summary, flags=re.DOTALL)
        summary = re.sub(r'思考:|摘要:|总结:', '', summary)
        summary = summary.strip()

        return summary if summary else text[:30] + "..."

    def _match_detail_from_summary(self, summary: str) -> List[str]:
        matched_details = set()
        for pattern, category in self.core_mappings.items():
            if pattern.strip() and re.search(pattern, summary, re.IGNORECASE):
                matched_details.add(category)
        return list(matched_details) if matched_details else ["无"]

    def _run(self, text: str) -> str:
        bert_result = self.bert_model.predict(text)
        is_malicious = bert_result["是否恶意诋毁"] == "是"
        summary = self._generate_summary(text, is_malicious)
        detail_pred = self._match_detail_from_summary(summary)

        return (
            f"1. 文本摘要：{summary}\n"
            f"2. 核心问题类型：{bert_result['核心问题类型']}\n"
            f"3. 问题细项：{'/'.join(detail_pred)}\n"
            f"4. 情感强度：{bert_result['情感强度']}\n"
            f"5. 是否恶意诋毁：{bert_result['是否恶意诋毁']}"
        )

    def _arun(self, text: str):
        raise NotImplementedError("不支持异步调用")


# 3. 初始化 Agent
def init_tourism_agent(
        bert_model_path: str,
        encoder_path: str,
        bert_pretrain_path: str,
        max_len: int = 256,
        vllm_url: str = "http://hpc.wisesoe.com:58001/v1",
        vllm_model: str = "deepseek-r1-distill-qwen-vllm"
):
    # 加载BERT模型
    try:
        bert_model = BertTourismModel(
            model_path=bert_model_path,
            encoder_path=encoder_path,
            bert_pretrain_path=bert_pretrain_path,
            max_len=max_len
        )
    except Exception as e:
        raise RuntimeError(f"BERT加载失败：{str(e)}")

    # 加载vLLM
    try:
        llm = ChatOpenAI(
            base_url=vllm_url,
            api_key="dummy_key",
            model_name=vllm_model,
            temperature=0.0,
            max_tokens=100,
            request_timeout=60
        )
        print(f"✅ vLLM加载成功（模型：{vllm_model}，地址：{vllm_url}）")
    except Exception as e:
        raise RuntimeError(f"vLLM连接失败：{str(e)}")

    # 初始化工具
    tools = [TourismBertTool(bert_model=bert_model, llm=llm)]

    # 修改后的Agent指令：判断是否含有负面情绪
    react_instructions = """
    严格遵循2步流程，每次仅执行1步，禁止混合输出！

    【步骤1：无工具结果时】
    仅判断用户输入是否含有负面情绪/投诉/抱怨/不满/问题：
    - 含有负面情绪：输出3行（格式严格）
      Thought: 用户输入含有负面情绪或问题描述，需调用tourism_bert_analyzer获取摘要和分析结果
      Action: tourism_bert_analyzer
      Action Input: [用户输入的完整文本]
    - 纯中性/正面情绪：输出2行
      Thought: 用户输入不含负面情绪或问题描述，无需调用工具
      Final Answer: 您的输入不包含需要分析的问题或负面情绪，无法进行舆情分析

    【步骤2：有工具结果时】
    仅基于工具返回的"文本摘要、核心问题、细项、情感、是否恶意"5项内容整理答案，不重复调用工具：
    Thought: 已获取工具结果（含文本摘要和匹配细项），整理为最终答案
    Final Answer: 根据旅游舆情分析：文本摘要为XXX，核心问题类型是XXX，问题细项包括XXX，情感强度为XXX，是否恶意诋毁为XXX（将XXX替换为工具返回的实际内容，用自然语言串联）

    禁止：步骤1输出Final Answer、步骤2输出Action、添加额外解释！
    """

    # 初始化Agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        return_intermediate_steps=True,
        handle_parsing_errors="继续执行下一步",
        agent_kwargs={"format_instructions": react_instructions}
    )

    return agent, bert_model


# 4. 交互测试
if __name__ == "__main__":
    CONFIG = {
        "bert_model_path": r"models/bert_tourism_best.pth",
        "encoder_path": r"models/bert_tourism_encoders.joblib",
        "bert_pretrain_path": r"models/bert-base-chinese",
        "max_len": 256,
        "vllm_url": r"http://hpc.wisesoe.com:58001/v1",
        "vllm_model": r"deepseek-r1-distill-qwen-vllm"
    }

    try:
        tourism_agent, bert_model = init_tourism_agent(**CONFIG)
        print("\n✅ 旅游舆情AI Agent初始化完成！")
        print("📌 示例输入：'山顶餐厅黄瓜卖10元一根，价格太贵，而且服务员态度很差'\n")
    except Exception as e:
        print(f"\n❌ 初始化失败：{str(e)}")
        exit()
    while True:
        user_input = input("你：").strip().strip("'\"")
        if user_input.lower() in ["退出", "quit", "exit"]:
            print("Agent：感谢使用，再见！")
            break
        if len(user_input) < 5:
            print("Agent：请输入至少5个字符的旅游文本（如'景区卫生间设施损坏'）\n")
            continue

        try:
            result = tourism_agent.invoke({"input": user_input})
            print(f"Agent：{result['output']}\n")

            # 处理工具原始输出，移除<think>部分
            raw_output = result['intermediate_steps'][0][1] if result.get('intermediate_steps') else ""

            # 查找文本摘要开始位置
            summary_start = raw_output.find("1. 文本摘要：")
            if summary_start != -1:
                # 查找<think>开始和结束的位置
                think_start = raw_output.find("<think>", summary_start)
                think_end = raw_output.find("</think>", summary_start)

                if think_start != -1 and think_end != -1:
                    # 移除<think>部分
                    cleaned_output = raw_output[:think_start] + raw_output[think_end + 8:]
                    print(f"📝 工具原始输出：{cleaned_output}\n")
                else:
                    print(f"📝 工具原始输出：{raw_output}\n")
            elif raw_output:
                print(f"📝 工具原始输出：{raw_output}\n")

        except Exception as e:
            print(f"Agent：分析失败：{str(e)}\n")
