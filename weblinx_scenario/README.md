# WebLINX Green Agent for AgentBeats

超级简化版的 WebLINX 实现，基于官方 template 和队友的 MiniWob 代码。

## 📁 文件结构

```
weblinx_agentbeats/
├── weblinx_green_agent/
│   ├── green_agent_card.toml    # Green Agent 配置
│   └── tools.py                  # Green Agent 工具函数
├── weblinx_purple_agent/
│   └── purple_agent_card.toml   # Purple Agent 配置
├── scenario.toml                 # 场景配置
└── README.md                     # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install agentbeats datasets weblinx
```

### 2. 设置环境变量

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 3. 启动 Agents

#### 方法 A: 使用 AgentBeats CLI（推荐）

```bash
# 在 weblinx_agentbeats 目录下运行
agentbeats run_scenario scenario.toml
```

#### 方法 B: 分别启动

**终端 1 - Green Agent:**
```bash
cd weblinx_green_agent
agentbeats run green_agent_card.toml \
  --launcher_host localhost \
  --launcher_port 9114 \
  --agent_host localhost \
  --agent_port 9115 \
  --model_type openai \
  --model_name gpt-4o-mini \
  --tools tools.py \
  --mcp http://localhost:9001/sse
```

**终端 2 - Purple Agent:**
```bash
cd weblinx_purple_agent
agentbeats run purple_agent_card.toml \
  --launcher_host localhost \
  --launcher_port 9110 \
  --agent_host localhost \
  --agent_port 9111 \
  --model_type openai \
  --model_name gpt-4o-mini \
  --mcp http://localhost:9001/sse
```

### 4. 注册到 AgentBeats 平台

1. 访问 https://agentbeats.org
2. 登录并进入 "Register Agent"
3. 填写 Green Agent 信息:
   - **Agent URL**: `http://YOUR_PUBLIC_IP:9115`
   - **Launcher URL**: `http://YOUR_PUBLIC_IP:9114`
4. 填写 Purple Agent 信息:
   - **Agent URL**: `http://YOUR_PUBLIC_IP:9111`
   - **Launcher URL**: `http://YOUR_PUBLIC_IP:9110`

### 5. 创建 Battle

在 AgentBeats 平台上:
1. 选择你的 WebLINX Green Agent
2. 选择你的 Purple Agent（或其他人的）
3. 开始评估！

## 🔧 工具函数说明

### Green Agent Tools

#### `reset_weblinx_env(split="validation")`
初始化 WebLINX 数据集

```python
result = reset_weblinx_env("validation")
# 返回: {"success": True, "total_tasks": 100}
```

#### `get_weblinx_task(task_id=0)`
获取指定任务

```python
task = get_weblinx_task(0)
# 返回: {"task_id": 0, "instruction": "...", "url": "..."}
```

#### `evaluate_purple_agent_action(agent_action)`
评估 Purple Agent 的动作

```python
result = evaluate_purple_agent_action("click [0.5, 0.3]")
# 返回: {"success": True, "score": 1.0}
```

#### `get_weblinx_statistics()`
获取总体统计

```python
stats = get_weblinx_statistics()
# 返回: {"success_rate": 0.8, "total_tasks": 10}
```

## 📊 数据集信息

WebLINX 使用 HuggingFace 的数据集，会自动下载和缓存：

- **Validation Split**: ~100 个任务
- **Test IID Split**: ~200 个任务

数据集包含:
- 真实网站的导航任务
- 多轮对话指令
- 期望的动作序列

## 🎯 评估逻辑

简单的字符串匹配评估:

1. **完全匹配**: score = 1.0 ✅
2. **动作类型匹配**: score = 0.5 ⚠️
3. **完全不匹配**: score = 0.0 ❌

## 🔍 本地测试

创建 `test_local.py`:

```python
import asyncio
from weblinx_green_agent.tools import (
    reset_weblinx_env,
    get_weblinx_task,
    evaluate_purple_agent_action,
    get_weblinx_statistics
)

async def test():
    # 1. 初始化
    result = await reset_weblinx_env("validation")
    print(result)
    
    # 2. 获取任务
    task = await get_weblinx_task(0)
    print(task)
    
    # 3. 模拟 Purple Agent 响应
    eval_result = await evaluate_purple_agent_action("click [0.5, 0.3]")
    print(eval_result)
    
    # 4. 获取统计
    stats = await get_weblinx_statistics()
    print(stats)

if __name__ == "__main__":
    asyncio.run(test())
```

运行测试:
```bash
python test_local.py
```

## 🐛 常见问题

### Q: 数据集下载太慢？
**A**: WebLINX 会自动缓存到 `~/.cache/huggingface/datasets/`，第一次会比较慢。

### Q: 评估不准确？
**A**: 当前使用简单字符串匹配。可以在 `tools.py` 中改进 `evaluate_purple_agent_action` 函数，使用语义相似度或更复杂的匹配逻辑。

### Q: 端口冲突？
**A**: 修改 `scenario.toml` 中的端口号。

### Q: 连接 MCP Server 失败？
**A**: 确保 MCP Server 在 `localhost:9001` 运行。

## 📝 进阶改进

### 1. 更智能的评估
```python
from difflib import SequenceMatcher

def advanced_evaluation(expected, actual):
    similarity = SequenceMatcher(None, expected, actual).ratio()
    return similarity
```

### 2. 支持多步骤任务
```python
# 在 tools.py 中添加
@ab.tool
async def evaluate_multi_step(actions_list: list) -> str:
    """评估多步骤动作序列"""
    pass
```

### 3. 添加更多统计指标
```python
# 在 get_weblinx_statistics 中添加
stats["average_similarity"] = ...
stats["median_score"] = ...
```

## 🎓 学习资源

- [WebLINX 论文](https://arxiv.org/abs/2402.05930)
- [WebLINX GitHub](https://github.com/McGill-NLP/weblinx)
- [AgentBeats 文档](https://docs.agentbeats.org/)
- [AgentBeats GitHub](https://github.com/agentbeats/agentbeats)

## 📄 许可证

本项目遵循 MIT 许可证。WebLINX 数据集遵循 CC BY-NC-SA 4.0 许可证。

---

**祝你在 AgentX-AgentBeats 竞赛中取得好成绩！** 🏆
