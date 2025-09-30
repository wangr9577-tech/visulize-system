from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
import uuid
from ai_agent封装 import init_tourism_agent  # 导入现有Agent初始化逻辑
from fastapi.middleware.cors import CORSMiddleware

# 初始化FastAPI应用
app = FastAPI(title="旅游舆情分析API（OpenAI兼容）")

# 配置CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# 1. 加载AI Agent（服务启动时初始化）
# --------------------------
CONFIG = {
    "bert_model_path": "models/bert_tourism_best.pth",
    "encoder_path": "models/bert_tourism_encoders.joblib",
    "bert_pretrain_path": r"models/bert-base-chinese",
    "max_len": 256,
    "vllm_url": "http://hpc.wisesoe.com:58001/v1",
    "vllm_model": "deepseek-r1-distill-qwen-vllm"
}

try:
    tourism_agent, bert_model = init_tourism_agent(** CONFIG)
    print("✅ AI Agent初始化成功（OpenAI风格API）")
except Exception as e:
    raise RuntimeError(f"Agent初始化失败：{str(e)}")

# --------------------------
# 2. 定义OpenAI风格的请求/响应模型
# --------------------------
class Message(BaseModel):
    role: str  # 仅支持"user"（用户输入）
    content: str  # 用户输入的旅游文本

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="tourism-sentiment-analyzer", description="模型名称（固定值）")
    messages: List[Message] = Field(description="对话历史，最后一条为用户输入")
    temperature: float = Field(default=0.0, ge=0.0, le=1.0, description="温度参数（固定为0，确保结果稳定）")
    max_tokens: Optional[int] = Field(default=500, description="最大响应长度")

class Choice(BaseModel):
    index: int
    message: Message  # 响应消息（role为"assistant"）
    finish_reason: str = "stop"

class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:16]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Choice]
    usage: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

# --------------------------
# 3. 实现OpenAI风格接口
# --------------------------
@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    # 1. 验证请求合法性
    if len(request.messages) == 0:
        raise HTTPException(status_code=400, detail="messages不能为空")
    user_message = request.messages[-1]
    if user_message.role != "user":
        raise HTTPException(status_code=400, detail="最后一条消息必须为user角色")
    user_input = user_message.content.strip()
    if len(user_input) < 5:
        raise HTTPException(status_code=400, detail="输入文本至少5个字符")

    # 2. 调用AI Agent处理
    try:
        result = tourism_agent.invoke({"input": user_input})
        agent_response = result["output"]  # Agent返回的最终答案
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败：{str(e)}")

    # 3. 构造OpenAI风格响应
    return ChatCompletionResponse(
        model=request.model,
        choices=[
            Choice(
                index=0,
                message=Message(role="assistant", content=agent_response)
            )
        ]
    )

# 基础启动（前台运行，关闭终端则服务停止）
# uvicorn openai_api:app --host 0.0.0.0 --port 8000