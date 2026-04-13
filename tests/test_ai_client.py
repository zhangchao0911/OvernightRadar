"""
AI 客户端测试
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_claude_client_initialization():
    """测试 Claude 客户端初始化"""
    from ai_client import AIClient, Provider

    # 使用 mock key
    client = AIClient(provider=Provider.CLAUDE, api_key="test_key")
    assert client.provider == Provider.CLAUDE
    assert client.api_key == "test_key"


def test_openai_client_initialization():
    """测试 OpenAI 客户端初始化"""
    from ai_client import AIClient, Provider

    client = AIClient(provider=Provider.OPENAI, api_key="test_key")
    assert client.provider == Provider.OPENAI


def test_build_prompt():
    """测试 Prompt 构建"""
    from ai_client import AIClient, Provider

    client = AIClient(provider=Provider.CLAUDE, api_key="test")

    news = [
        {"headline": "Test News 1", "summary": "Summary 1", "source": "Test Source"},
        {"headline": "Test News 2", "summary": "Summary 2", "source": "Test Source"}
    ]

    prompt = client.build_signal_prompt(news)

    assert "Test News 1" in prompt
    assert "Test News 2" in prompt
    assert "JSON" in prompt


def test_default_model():
    """测试默认模型选择"""
    from ai_client import AIClient, Provider

    claude_client = AIClient(provider=Provider.CLAUDE, api_key="test")
    assert "claude" in claude_client.model.lower()

    openai_client = AIClient(provider=Provider.OPENAI, api_key="test")
    assert "gpt" in openai_client.model.lower()


def test_custom_model():
    """测试自定义模型"""
    from ai_client import AIClient, Provider

    client = AIClient(provider=Provider.CLAUDE, api_key="test", model="claude-3-opus")
    assert client.model == "claude-3-opus"


def test_build_prompt_limit():
    """测试 Prompt 构建限制新闻数量"""
    from ai_client import AIClient, Provider

    client = AIClient(provider=Provider.CLAUDE, api_key="test")

    # 生成 25 条新闻（超过 20 条限制）
    news = [
        {"headline": f"News {i}", "summary": f"Summary {i}", "source": "Test"}
        for i in range(1, 26)  # 生成 News 1 到 News 25
    ]

    prompt = client.build_signal_prompt(news)

    # 应该只包含前 20 条 (News 1 - News 20)
    assert "News 1" in prompt
    assert "News 20" in prompt
    assert "News 21" not in prompt
    assert "News 25" not in prompt
