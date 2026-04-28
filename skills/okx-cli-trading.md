---
name: okx-cli-trading
description: OKX Agent Trade Kit CLI 操作手册 — 下单、平仓、查仓位、JSON vs 纯文本响应处理
tags: [devops, crypto, trading, okx]
---

# OKX Agent Trade Kit — CLI 交易操作

## 安装
```bash
npm install -g @okx_ai/okx-trade-mcp @okx_ai/okx-trade-cli
```
配置文件：`~/.okx/config.toml`（passphrase不含中文）

## 常用命令

```bash
# 查余额
okx --json account balance --profile demo

# 设置杠杆
okx --json swap leverage --instId BTC-USDT-SWAP --lever 10 --mgnMode cross

# 市价开仓（永续）
okx --json --demo swap place --instId BTC-USDT-SWAP --side buy --ordType market \
  --sz 0.01 --tdMode cross --posSide long \
  --slTriggerPx 95000 --slOrdPx -1 \
  --tpTriggerPx 110000 --tpOrdPx -1

# 平仓（必须指定 posSide，否则报 "Position doesn't exist"）
okx --json --demo swap close --instId BTC-USDT-SWAP --mgnMode cross --posSide long

# 查持仓（swap positions 返回纯数组）
okx --json --demo swap positions
okx --json --demo swap positions BTC-USDT-SWAP

# 查行情（使用 ticker，不是 price）
okx --json --demo market ticker BTC-USDT-SWAP

# 查帐户持仓（account 模块也可）
okx --json --demo account positions --instType SWAP
```

## 配置与环境
配置文件：`~/.okx/config.toml`（passphrase 不含中文）

- `OKX_PROFILE=demo` 环境变量可指定 profile
- `--demo` / `--live` 可覆盖 profile 设置，与环境变量互不冲突
- 当 profile 已设置 `demo = true` 时，`swap positions` 可能无需 `--demo` 也返回模拟盘数据；但建议显式加 `--demo` 避免模糊

## 平仓必须指定 posSide
`swap close` 省略 `--posSide` 或传错时会报 `Position doesn't exist`。必须与当前持仓的 `posSide`（`long`/`short`）一致。

## ⚠️ 优先使用 `--json` 获取结构化输出

OKX CLI v1.3.1+ 支持 `--json` 全局选项，返回可解析的 JSON。推荐始终使用：

```bash
okx --json --demo swap positions
okx --json --demo market ticker BTC-USDT-SWAP
```

### `--json` 输出陷阱：部分命令返回原始数组

`swap positions`、`market ticker` 等命令用 `--json` 时直接返回 `[]` 或 `[{...}]`，不是 `{data: [...]}` 包装：

```python
import subprocess, json, os

def run_okx(args, profile="demo"):
    cmd = ["okx", "--json"] + args
    r = subprocess.run(cmd, capture_output=True, text=True,
                       env={**os.environ, "OKX_PROFILE": profile})
    out = r.stdout.strip()
    try:
        parsed = json.loads(out)
        if isinstance(parsed, list):
            return {"data": parsed}   # 统一包装成字典
        return parsed
    except:
        # 无 --json 时的纯文本兜底
        if "Order placed" in out or "(OK)" in out or "closed" in out.lower():
            return {"raw": out, "ok": True}
        return {"raw": out, "stderr": r.stderr, "rc": r.returncode}
```

## 最小下单单位（各币种 lot size 不同）

| 合约 | lotSz / minSz |
|------|---------------|
| BTC-USDT-SWAP | 0.01 |
| ETH-USDT-SWAP | 0.01 |
| SOL-USDT-SWAP | 0.01 |
| DOGE-USDT-SWAP | 0.01 |
| XRP-USDT-SWAP | 0.01 |
| ADA-USDT-SWAP | 0.1 |
| AVAX-USDT-SWAP | 0.1 |
| LINK-USDT-SWAP | 0.1 |
| BNB-USDT-SWAP | 1 |
| DOT-USDT-SWAP | 1 |

脚本中硬编码 `0.01` 会在 BNB、DOT 等币种上报 `sCode 51121`（Order quantity must be a multiple of the lot size）。建议维护 `SYMBOL_SIZE_MAP` 或下单前查 `https://www.okx.com/api/v5/public/instruments?instType=SWAP`。

## ⚠️ CLI 参数陷阱

### 1. 负值参数必须用 `=` 连接
`--slOrdPx -1` 会被 CLI parser 当成 `--slOrdPx` 后面跟着一个名为 `-1` 的 flag，触发 "argument is ambiguous"。正确写法：
```bash
--slOrdPx=-1 --tpOrdPx=-1
```

### 2. npm update 横幅污染 stdout
okx CLI v1.3.x 在 stdout 顶部输出 npm update 提示（如 `Update available for @okx_ai/okx-trade-cli: 1.3.1 → 1.3.2`），再用 `--json` 也会把这段文字放在 JSON 前面，导致 `json.loads()` 直接抛错。

**修复方法**：提取第一个 `[` 或 `{` 之后再解析：
```python
def extract_json(text):
    start = next((i for i, ch in enumerate(text) if ch in ('{', '[')), -1)
    if start >= 0:
        return json.loads(text[start:])
    raise ValueError("No JSON found")
```

结合 "返回原始数组" 的陷阱，完整的 `run_okx` 封装：
```python
import subprocess, json, os

def run_okx(args, profile="demo", timeout=15):
    cmd = ["okx", "--json"] + args
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                       env={**os.environ, "OKX_PROFILE": profile})
    out = r.stdout.strip()
    # 1. 去掉 npm update 横幅
    start = next((i for i, ch in enumerate(out) if ch in ('{', '[')), -1)
    if start >= 0:
        try:
            parsed = json.loads(out[start:])
            # 2. 数组结果统一包装
            return {"data": parsed} if isinstance(parsed, list) else parsed
        except json.JSONDecodeError:
            pass
    # 纯文本成功响应
    if "Order placed" in out or "(OK)" in out or "closed" in out.lower():
        return {"raw": out, "ok": True}
    return {"raw": out, "stderr": r.stderr, "rc": r.returncode}
```
