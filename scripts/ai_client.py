"""
AI 客户端封装 - 支持 Claude/OpenAI

核心功能：
1. 统一的 AI 客户端接口，支持 Claude 和 OpenAI
2. 构建交易信号生成的 Prompt
3. 调用 AI API 并解析 JSON 响应
4. 错误处理和容错机制

使用示例：
    provider, api_key = load_api_key()
    client = AIClient(provider=provider, api_key=api_key)
    signals = client.generate_signals(news_list)
"""
import os
import json
from enum import Enum
from typing import List, Dict, Optional, Tuple
import requests


class Provider(Enum):
    """AI 服务提供商"""
    CLAUDE = "claude"
    OPENAI = "openai"


class AIClient:
    """统一的 AI 客户端接口"""

    def __init__(self, provider: Provider, api_key: str, model: Optional[str] = None):
        """
        初始化 AI 客户端

        Args:
            provider: AI 服务提供商 (Provider.CLAUDE 或 Provider.OPENAI)
            api_key: API 密钥
            model: 模型名称（可选，使用默认值）
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model or self._default_model()

    def _default_model(self) -> str:
        """
        获取默认模型名称

        Returns:
            默认模型名称字符串
        """
        if self.provider == Provider.CLAUDE:
            return "claude-3-5-sonnet-20241022"
        elif self.provider == Provider.OPENAI:
            return "gpt-4o"
        return "unknown"

    def build_signal_prompt(self, news: List[Dict]) -> str:
        """
        构建信号生成 Prompt

        设计思路：
        1. 提供结构化的新闻列表（编号 + 标题 + 来源 + 摘要）
        2. 明确输出格式要求（JSON）
        3. 强调信号的质量要求（可执行性、具体性）

        Args:
            news: 新闻列表，每条包含 headline, summary, source 等

        Returns:
            完整的 Prompt 字符串
        """
        # ─── 构建新闻文本 ───
        # 限制最多 20 条新闻，避免 token 超限
        news_text = "\n".join([
            f"{i+1}. {n.get('headline', '')} ({n.get('source', '')})\n"
            f"   {n.get('summary', '')[:100]}..."
            for i, n in enumerate(news[:20])
        ])

        # ─── 构建 Prompt ───
        return f"""你是一位专业的美股交易分析师。以下是今日美股相关新闻：

{news_text}

请分析这些新闻，输出 3-5 条交易信号。

要求：
1. 每条信号必须包含：title, direction, sectors, action, reason
2. action 必须是具体可执行的建议（条件 + 动作），如"若高开>2%不追，低开可关注"
3. 只输出真正有信号价值的新闻，忽略噪音
4. 按重要性降序排列

输出格式（必须是有效的 JSON，不要包含其他文字）：
[
  {{
    "title": "简短标题",
    "direction": "利多/利空",
    "sectors": ["板块1", "板块2"],
    "action": "若高开>2%不追，低开可关注",
    "reason": "交易逻辑说明"
  }}
]
"""

    def generate_signals(self, news: List[Dict]) -> List[Dict]:
        """
        调用 AI 生成交易信号

        Args:
            news: 新闻列表

        Returns:
            生成的信号列表，失败时返回空列表
        """
        prompt = self.build_signal_prompt(news)

        if self.provider == Provider.CLAUDE:
            return self._call_claude(prompt)
        elif self.provider == Provider.OPENAI:
            return self._call_openai(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _call_claude(self, prompt: str) -> List[Dict]:
        """
        调用 Claude API

        API 文档: https://docs.anthropic.com/claude/reference/messages_post

        Args:
            prompt: 完整的 Prompt 字符串

        Returns:
            解析后的信号列表，失败时返回空列表
        """
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": self.model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            result = resp.json()

            # Claude 响应格式: { content: [{ type: "text", text: "..." }] }
            content = result.get("content", [{}])[0].get("text", "")
            return self._parse_json_response(content)
        except Exception as e:
            print(f"ERROR: Claude API 调用失败 - {e}")
            return []

    def _call_openai(self, prompt: str) -> List[Dict]:
        """
        调用 OpenAI API

        API 文档: https://platform.openai.com/docs/api-reference/chat/create

        Args:
            prompt: 完整的 Prompt 字符串

        Returns:
            解析后的信号列表，失败时返回空列表
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "authorization": f"Bearer {self.api_key}",
            "content-type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3  # 降低随机性，提高稳定性
        }

        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            result = resp.json()

            # OpenAI 响应格式: { choices: [{ message: { content: "..." } }] }
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return self._parse_json_response(content)
        except Exception as e:
            print(f"ERROR: OpenAI API 调用失败 - {e}")
            return []

    def _parse_json_response(self, content: str) -> List[Dict]:
        """
        从 AI 响应中解析 JSON

        AI 返回的内容可能有多种格式：
        1. 纯 JSON 字符串
        2. Markdown 代码块包裹的 JSON（```json ... ```）
        3. 普通代码块包裹的 JSON（``` ... ```）

        Args:
            content: AI 返回的原始文本

        Returns:
            解析后的信号列表，失败时返回空列表
        """
        # ─── 尝试直接解析 ───
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # ─── 尝试提取 ```json ... ``` 代码块 ───
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            try:
                return json.loads(content[start:end].strip())
            except (json.JSONDecodeError, ValueError):
                pass

        # ─── 尝试提取 ``` ... ``` 代码块 ───
        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            try:
                return json.loads(content[start:end].strip())
            except (json.JSONDecodeError, ValueError):
                pass

        # ─── 所有尝试都失败 ───
        print("ERROR: 无法解析 AI 响应为 JSON")
        print(f"Content: {content[:500]}")
        return []


def load_api_key() -> Tuple[Optional[Provider], str]:
    """
    从环境变量加载 AI API key

    优先级：
    1. ANTHROPIC_API_KEY (Claude)
    2. OPENAI_API_KEY (OpenAI)

    Returns:
        (Provider, api_key) 元组，如果没有可用的 key 则返回 (None, "")
    """
    # 优先使用 Claude
    claude_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if claude_key:
        return Provider.CLAUDE, claude_key

    # 其次使用 OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_key:
        return Provider.OPENAI, openai_key

    return None, ""
