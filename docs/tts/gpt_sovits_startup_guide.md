# GPT-SoVITS V4 API 服务部署手册

> [!IMPORTANT]
> **Windows 前置要求**：安装步骤中有多个包需要 C++ 编译器，请在开始前完成以下两项工具的安装，否则后续步骤大概率失败。

> 适用场景：从 GitHub 克隆最新代码，使用已训练好的 V4 角色模型，作为 API 服务供其他项目调用。

---

## 第一步：克隆代码

```bash
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS
```

---

## 第二步：创建 Conda 环境

> [!IMPORTANT]
> **必须使用 Python 3.10**，不要用 3.11/3.12/3.13。
> 原因：`numpy<2.0`（项目硬依赖）在 Python 3.11+ 没有预编译包，会触发 C++ 源码编译报错。

```bash
conda create -n gptSOVIT python=3.10 -y
conda activate gptSOVIT
```

---

## 第三步：安装 C++ 构建环境（Windows 必须）

> [!IMPORTANT]
> 此步骤是 **Windows 上必须完成的前置条件**，跳过会导致 `numpy`、`numba`、av 等多个包安装失败。

### 安装 Visual Studio Build Tools

1. 下载 **Visual Studio Build Tools**：
   [https://aka.ms/vs/17/release/vs_buildtools.exe](https://aka.ms/vs/17/release/vs_buildtools.exe)

2. 运行安装程序，勾选 **「使用 C++ 的桌面开发」** 工作负载

   必须包含以下组件（默认勾选即可）：
   - MSVC v143 编译器
   - Windows 10/11 SDK
   - CMake（可选但推荐）

3. 点击安装，等待完成（约 3-6 GB）

4. **安装完成后重启终端**（重要！环境变量需要刷新）

> [!TIP]
> 如果已安装完整版 Visual Studio（Community/Professional），则已自带 C++ 工具，跳过此步骤。
> 可以通过在终端输入 `cl` 验证是否已安装，有输出内容则说明已就绪。

---

## 第四步：安装 PyTorch

根据你的显卡情况二选一：

**有 NVIDIA 显卡（推荐，速度快）：**
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
```

**无显卡 / 仅 CPU（速度慢约 5-10 倍）：**
```bash
pip install torch torchaudio
```

---

## 第五步：安装依赖


在项目根目录创建 requirements_api.txt（精简版，去掉训练/WebUI/日韩语等不必要依赖）：

```
# Core ML
pytorch-lightning>=2.4
torchmetrics<=1.5
x_transformers
rotary_embedding_torch
peft<0.18.0

# Transformers
transformers>=4.43,<=4.50
sentencepiece

# 音频处理
soundfile
librosa==0.10.2
numba
scipy
numpy<2.0
ffmpeg-python
av>=11

# 中文文本处理
pypinyin
cn2an
jieba
fast_langdetect>=0.3.1
split-lang
wordsegment
g2p_en

# OpenCC 简繁转换（纯 Python 版，无需 C++ 编译）
opencc-python-reimplemented

# API 服务
fastapi[standard]>=0.115.2
uvicorn
pydantic<=2.10.6

# 其他工具
PyYAML
tqdm
chardet
matplotlib
```

```bash
pip install -r requirements_api.txt
```

> [!NOTE]
> `pyopenjtalk`（日文）和 `opencc`（原版）都需要 C++ 编译器，在 Windows 上会报错，已从列表中去除，不影响中文使用。

---

## 第五步：Windows 兼容补丁（jieba_fast）

`jieba_fast` 同样需要 C++ 编译，但项目代码里有 `import jieba_fast`。
解决方案：在项目根目录手动创建一个兼容包，让它指向标准 `jieba`。

```powershell
New-Item -ItemType Directory jieba_fast | Out-Null
```

**jieba_fast/__init__.py：**
```python
from jieba import *
from jieba import dt, re_han_default, analyse
import jieba as _jieba

cut = _jieba.cut
lcut = _jieba.lcut
cut_for_search = _jieba.cut_for_search
lcut_for_search = _jieba.lcut_for_search
add_word = _jieba.add_word
load_userdict = _jieba.load_userdict
set_dictionary = _jieba.set_dictionary
initialize = _jieba.initialize
```

**jieba_fast/posseg.py：**
```python
from jieba.posseg import *
from jieba.posseg import cut, lcut, POSTokenizer
```

---

## 第六步：准备模型文件

### 最终目录结构

```
GPT-SoVITS/
├── GPT_SoVITS/
│   ├── pretrained_models/
│   │   ├── chinese-hubert-base/           ← 必须（HuBERT 特征提取）
│   │   │   ├── config.json
│   │   │   ├── preprocessor_config.json
│   │   │   └── pytorch_model.bin
│   │   ├── chinese-roberta-wwm-ext-large/ ← 必须（BERT 文本特征）
│   │   │   ├── config.json
│   │   │   ├── pytorch_model.bin
│   │   │   └── tokenizer.json
│   │   ├── fast_langdetect/               ← 必须（语言检测）
│   │   │   └── lid.176.bin
│   │   └── gsv-v4-pretrained/             ← V4 必须（声码器）
│   │       └── vocoder.pth
│   └── configs/
│       └── tts_infer.yaml                 ← 需修改
└── jieba_fast/                            ← 第五步创建的补丁
    ├── __init__.py
    └── posseg.py
```

> [!WARNING]
> `s1v3.ckpt`、`s2Gv4.pth` 等**预训练底模不需要**下载，只有训练时才用到。
> 推理只需要上面四个目录中的文件。

### 文件下载（国内镜像）

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"

# 下载 BERT 和 HuBERT
huggingface-cli download lj1995/GPT-SoVITS `
  chinese-hubert-base chinese-roberta-wwm-ext-large `
  --local-dir GPT_SoVITS/pretrained_models

# 下载 V4 vocoder（约 56MB）
huggingface-cli download lj1995/GPT-SoVITS `
  "gsv-v4-pretrained/vocoder.pth" `
  --local-dir GPT_SoVITS/pretrained_models

# fast_langdetect/lid.176.bin 从 HuggingFace 手动下载后放入对应目录
```

---

## 第七步：配置模型路径

修改 GPT_SoVITS/configs/tts_infer.yaml，将 custom 节点改为你的角色模型绝对路径：

```yaml
custom:
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cuda        # 无 GPU 改为 cpu，同时 is_half 改为 false
  is_half: true       # CPU 模式必须为 false
  t2s_weights_path: e:/你的路径/角色名/角色名-eXX.ckpt
  version: v4
  vits_weights_path: e:/你的路径/角色名/角色名_eXX_sXXX_lXX.pth
```

---

## 第八步：启动 API

```bash
conda activate gptSOVIT
cd e:\你的路径\GPT-SoVITS
python api_v2.py -a 0.0.0.0 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

看到以下输出即启动成功 ✅：
```
INFO:     Uvicorn running on http://0.0.0.0:9880 (Press CTRL+C to quit)
```

> 首次启动会加载模型，需等待约 10-30 秒。

---

## 一键启动脚本（放桌面用）

创建 `start_tts_api.bat`：

```bat
@echo off
call conda activate gptSOVIT
cd /d C:\YourPath\tts\GPT-SoVITS
python api_v2.py -a 0.0.0.0 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
pause
```

---

## API 调用示例

### Python

```python
import requests

TTS_API = "http://127.0.0.1:9880"
REF_AUDIO = r"e:/你的路径/角色名/reference_audios/中文/emotions/参考音频.wav"
REF_TEXT  = "参考音频对应的文字内容"

def synthesize(text: str) -> bytes:
    resp = requests.post(f"{TTS_API}/tts", json={
        "text": text,
        "text_lang": "zh",
        "ref_audio_path": REF_AUDIO,
        "prompt_text": REF_TEXT,
        "prompt_lang": "zh",
        "media_type": "wav",
        "streaming_mode": False,
        "speed_factor": 1.0,
    }, timeout=60)
    if resp.status_code == 200:
        return resp.content  # wav 二进制
    raise Exception(resp.json())
```

### JavaScript（Node.js）

```javascript
const TTS_API = "http://127.0.0.1:9880";

async function synthesize(text) {
  const res = await fetch(`${TTS_API}/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      text_lang: "zh",
      ref_audio_path: "e:/你的路径/参考音频.wav",
      prompt_text: "参考音频对应的文字",
      prompt_lang: "zh",
      media_type: "wav",
      streaming_mode: false,
    }),
  });
  if (!res.ok) throw new Error(await res.text());
  return Buffer.from(await res.arrayBuffer());
}
```

---

## 其他常用接口

| 接口 | 作用 |
|------|------|
| `GET /set_gpt_weights?weights_path=xxx` | 热切换角色 GPT 模型 |
| `GET /set_sovits_weights?weights_path=xxx` | 热切换角色 SoVITS 模型 |
| `GET /set_refer_audio?refer_audio_path=xxx` | 预设参考音频 |
| `GET /control?command=restart` | 重启服务 |

---

## 常见报错速查

| 报错 | 原因 | 解决 |
|------|------|------|
| `No module named 'X'` | 缺少 Python 包 | `pip install X` |
| `jieba_fast is not a package` | 补丁为单个 .py 文件 | 确认第五步创建的是**目录**结构 |
| `Failed to build jieba_fast` | 需要 C++ 编译器 | 使用第五步手动补丁，不要 pip 安装 |
| `numpy<2.0` 构建失败 | Python >= 3.11 | 改用 Python **3.10** 创建 conda 环境 |
| `ref_audio_path is required` | API 调用缺少参考音频 | ref_audio_path 必传，且路径文件须存在 |
| vocoder 相关报错 | 缺少 V4 声码器 | 下载 `gsv-v4-pretrained/vocoder.pth` |
