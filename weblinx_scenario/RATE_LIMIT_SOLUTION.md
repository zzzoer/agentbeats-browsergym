# 🚨 HuggingFace 速率限制解决方案

## 问题诊断

你遇到的错误：
```
429 Client Error: Too Many Requests
达到限制: 5000 requests / 5 分钟
```

**原因**：下载 WebLINX-full 数据集太快，触发了 HuggingFace 的速率限制。

---

## 🎯 推荐解决方案（按优先级）

### ✅ 方案 1: 在线使用（最推荐！不需要下载）

**优点**：
- 🚀 立即可用
- 💾 不占用本地空间
- ⚡ 自动缓存常用数据
- ❌ 不会触发速率限制

**使用方法**：

```python
# test_online_weblinx.py
from datasets import load_dataset

# 直接在线加载（HuggingFace 自动处理缓存）
valid = load_dataset("McGill-NLP/weblinx", split="validation")
print(f"✅ 加载成功！共 {len(valid)} 个样本")

# 正常使用
sample = valid[0]
print(sample["instruction"])
```

**运行**：
```bash
python test_online_weblinx.py
```

**💡 这就是你的 tools.py 中使用的方式！不需要改动！**

---

### ✅ 方案 2: 选择性下载（快速且安全）

**适合**：想要离线使用部分数据

**优点**：
- ⚡ 几分钟完成
- 💾 只下载需要的
- ✅ 不会触发限制

**使用方法**：

```bash
python download_weblinx_selective.py
```

选择下载数量：
- 测试用：3个演示（1分钟）
- 开发用：10个演示（5分钟）
- 完整用：50个演示（20分钟）

---

### ✅ 方案 3: 等待 + 重试（简单但慢）

**适合**：已经下载了一部分，想继续

**使用方法**：

```bash
# 等待 5-10 分钟后运行
python download_weblinx_safe.py
```

**特点**：
- 自动重试 5 次
- 支持断点续传
- 单线程下载（慢但稳）

---

### ✅ 方案 4: 使用 HuggingFace Token（长期方案）

**适合**：经常下载大数据集

**步骤**：

1. **获取 Token**：
   - 访问：https://huggingface.co/settings/tokens
   - 点击 "New token"
   - 选择 "Read" 权限
   - 复制 token

2. **设置 Token**：
```bash
# Windows (PowerShell)
$env:HF_TOKEN="your_token_here"

# Linux/Mac
export HF_TOKEN="your_token_here"
```

3. **下载**：
```bash
python download_weblinx_with_token.py
```

**优点**：
- 更高的速率限制
- 支持私有数据集
- 免费用户也有提升

---

## 🎯 我的建议

### 对于你的情况：

```
✅ 最佳方案：直接使用在线模式
   → 运行 test_online_weblinx.py
   → 你的 tools.py 已经是这种方式！

❌ 不推荐：下载完整数据集
   → 很大（2-3GB）
   → 容易触发限制
   → 实际不需要
```

---

## 📝 具体操作步骤

### Step 1: 测试在线模式

```bash
cd D:\Agentbeats
python test_online_weblinx.py
```

**预期输出**：
```
WebLINX 在线加载测试
加载 validation 数据集...
✅ 成功！共 XXX 个样本
```

### Step 2: 运行你的代码

```bash
python test_local.py
```

**应该正常工作！** 因为你的 `tools.py` 已经使用在线模式：

```python
# weblinx_green_agent/tools.py
weblinx_dataset = load_dataset("McGill-NLP/weblinx", split=split)
# ↑ 这已经是在线模式！
```

---

## 🔍 如果仍想下载数据集

### 选项 A: 等待并重试（简单）

```bash
# 1. 等待 10 分钟
# 2. 运行：
python download_weblinx_safe.py
```

### 选项 B: 选择性下载（推荐）

```bash
python download_weblinx_selective.py
# 选择 "1" 或 "2"（测试或开发用）
```

### 选项 C: 使用 Token（长期）

```bash
# 1. 获取 token (https://huggingface.co/settings/tokens)
# 2. 设置环境变量
export HF_TOKEN="hf_xxxxxxxxxxxx"
# 3. 下载
python download_weblinx_with_token.py
```

---

## 💡 常见问题

### Q: 我必须下载数据集吗？
**A**: 不！在线模式就够了。HuggingFace 会自动缓存你访问的数据。

### Q: 在线模式会很慢吗？
**A**: 第一次访问会稍慢，之后会被缓存，速度很快。

### Q: 缓存在哪里？
**A**: `C:\Users\你的用户名\.cache\huggingface\datasets\`

### Q: 如何清理缓存？
**A**: 删除上面的目录，或者：
```python
from datasets import clear_caching_enabled
clear_caching_enabled()
```

### Q: 429 错误多久恢复？
**A**: 通常 5-10 分钟。速率限制是滚动窗口。

### Q: 可以用代理吗？
**A**: 可以，但可能仍会触发限制。不如用在线模式。

---

## 🎓 技术细节

### 为什么会触发 429？

```python
# ❌ 这样会触发：多线程下载完整数据集
snapshot_download(
    repo_id="McGill-NLP/WebLINX-full",
    max_workers=8  # 太多并发请求！
)

# ✅ 这样不会：单线程 + 小数据
snapshot_download(
    repo_id="McGill-NLP/WebLINX-full",
    max_workers=1,
    allow_patterns=["demonstrations/demo1/*"]  # 只下载一个
)

# ✅ 最好的方式：在线使用
load_dataset("McGill-NLP/weblinx", split="validation")
```

### 速率限制详情

| 用户类型 | 限制 |
|---------|------|
| 匿名 | 5,000 requests / 5 分钟 |
| 免费 Token | 10,000 requests / 5 分钟 |
| Pro ($9/月) | 100,000 requests / 5 分钟 |

---

## 📊 方案对比

| 方案 | 时间 | 空间 | 速率限制风险 | 推荐度 |
|------|------|------|-------------|--------|
| 在线使用 | 0秒 | ~100MB缓存 | ❌ 无 | ⭐⭐⭐⭐⭐ |
| 选择性下载 | 5分钟 | ~500MB | ⚠️ 低 | ⭐⭐⭐⭐ |
| 等待重试 | 30-60分钟 | 2-3GB | ⚠️ 中 | ⭐⭐⭐ |
| 完整下载+Token | 20-40分钟 | 2-3GB | ⚠️ 低 | ⭐⭐ |

---

## 🚀 立即行动

### 1分钟快速测试：
```bash
python test_online_weblinx.py
```

### 5分钟开始开发：
```bash
python test_local.py
```

### 不需要其他操作！

---

## 📞 如果还有问题

1. 检查 `tools.py` 是否已经使用在线模式（应该是的）
2. 确认网络连接正常
3. 等待 10 分钟后再试
4. 考虑获取 HuggingFace Token

---

**总结**：你的代码已经使用在线模式，不需要下载完整数据集！直接运行 `test_local.py` 就能工作！🎉
