# GPT-SoVITS API 接口文档

**Base URL**: `http://127.0.0.1:9880`  
**交互式文档**: `http://127.0.0.1:9880/docs`

---

## POST /tts — 文本转语音（主接口）

### 请求

```http
POST http://127.0.0.1:9880/tts
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `text` | string | ✅ | — | 要合成的文字 |
| `text_lang` | string | ✅ | — | 文字语言：`zh` / [en](file:///e:/workspace/yiluomu/tts/GPT-SoVITS/GPT_SoVITS/TTS_infer_pack/TTS.py#63-65) / `ja` / `auto` |
| [ref_audio_path](file:///e:/workspace/yiluomu/tts/GPT-SoVITS/GPT_SoVITS/TTS_infer_pack/TTS.py#762-764) | string | ✅ | — | 参考音频**绝对路径**（用于声音克隆） |
| `prompt_lang` | string | ✅ | — | 参考音频语言：`zh` / [en](file:///e:/workspace/yiluomu/tts/GPT-SoVITS/GPT_SoVITS/TTS_infer_pack/TTS.py#63-65) / `ja` |
| `prompt_text` | string | ❌ | `""` | 参考音频对应的文字（填了效果更好） |
| `media_type` | string | ❌ | [wav](file:///e:/workspace/yiluomu/tts/v4/%E5%85%AB%E9%87%8D%E6%A8%B1/reference_audios/%E4%B8%AD%E6%96%87/emotions/%E3%80%90%E9%BB%98%E8%AE%A4%E3%80%91%E8%BF%99%E4%B8%AA%E8%BA%AB%E4%BD%93%E4%BC%BC%E4%B9%8E%E4%B8%8D%E4%BC%9A%E8%80%81%E5%8E%BB%EF%BC%8C%E4%BD%86%E6%88%91%E6%83%B3%E8%A7%81%E7%9A%84%E4%BA%BA%EF%BC%8C%E5%8D%B4%E9%83%BD%E7%A6%BB%E5%8E%BB%E4%BA%86%E3%80%82.wav) | 返回格式：[wav](file:///e:/workspace/yiluomu/tts/v4/%E5%85%AB%E9%87%8D%E6%A8%B1/reference_audios/%E4%B8%AD%E6%96%87/emotions/%E3%80%90%E9%BB%98%E8%AE%A4%E3%80%91%E8%BF%99%E4%B8%AA%E8%BA%AB%E4%BD%93%E4%BC%BC%E4%B9%8E%E4%B8%8D%E4%BC%9A%E8%80%81%E5%8E%BB%EF%BC%8C%E4%BD%86%E6%88%91%E6%83%B3%E8%A7%81%E7%9A%84%E4%BA%BA%EF%BC%8C%E5%8D%B4%E9%83%BD%E7%A6%BB%E5%8E%BB%E4%BA%86%E3%80%82.wav) / [ogg](file:///e:/workspace/yiluomu/tts/GPT-SoVITS/api_v2.py#181-225) / [aac](file:///e:/workspace/yiluomu/tts/GPT-SoVITS/api_v2.py#238-266) / [raw](file:///e:/workspace/yiluomu/tts/GPT-SoVITS/api_v2.py#227-230) |
| `streaming_mode` | bool/int | ❌ | `false` | 流式输出模式（见下方说明） |
| `speed_factor` | float | ❌ | `1.0` | 语速倍率（0.5 = 慢一半，2.0 = 快一倍） |
| `top_k` | int | ❌ | `15` | 采样 top-k |
| `top_p` | float | ❌ | `1.0` | 采样 top-p |
| `temperature` | float | ❌ | `1.0` | 采样温度 |
| [seed](file:///e:/workspace/yiluomu/tts/GPT-SoVITS/GPT_SoVITS/TTS_infer_pack/TTS.py#194-215) | int | ❌ | `-1` | 随机种子（-1 = 随机，固定值 = 可复现） |
| `batch_size` | int | ❌ | `1` | 批处理大小 |
| `sample_steps` | int | ❌ | `32` | V4 模型采样步数（越高越慢但质量更好） |

#### streaming_mode 说明

| 值 | 行为 |
|----|------|
| `false` / `0` | 等待完整音频生成后一次性返回（推荐） |
| `true` / `1` | 流式返回，最高质量，响应最慢 |
| `2` | 流式返回，中等质量，响应较快 |
| `3` | 流式返回，较低质量，响应最快 |

### 响应

- **成功**：直接返回音频二进制流，HTTP 200，Content-Type: `audio/wav`
- **失败**：返回 JSON，HTTP 400

```json
{ "message": "错误信息", "Exception": "详细异常" }
```

### 示例

```python
import requests

resp = requests.post("http://127.0.0.1:9880/tts", json={
    "text": "晚上好，依洛沐。夜色渐深了，要进来坐坐吗。",
    "text_lang": "zh",
    "ref_audio_path": "e:/workspace/yiluomu/tts/v4/八重樱/reference_audios/中文/emotions/【默认】这个身体似乎不会老去，但我想见的人，却都离去了。.wav",
    "prompt_text": "这个身体似乎不会老去，但我想见的人，却都离去了。",
    "prompt_lang": "zh",
    "media_type": "wav",
    "streaming_mode": False,
    "speed_factor": 1.0,
}, timeout=60)

# 保存音频
with open("output.wav", "wb") as f:
    f.write(resp.content)
```

```javascript
const resp = await fetch("http://127.0.0.1:9880/tts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    text: "晚上好，依洛沐。",
    text_lang: "zh",
    ref_audio_path: "e:/workspace/yiluomu/tts/v4/八重樱/reference_audios/中文/emotions/【默认】这个身体似乎不会老去，但我想见的人，却都离去了。.wav",
    prompt_text: "这个身体似乎不会老去，但我想见的人，却都离去了。",
    prompt_lang: "zh",
    media_type: "wav",
    streaming_mode: false,
  }),
});
const audioBuffer = await resp.arrayBuffer();
```

---

## GET /tts — 文本转语音（GET 版）

与 POST 相同，参数放 URL query string，适合简单测试：

```
GET http://127.0.0.1:9880/tts?text=你好&text_lang=zh&ref_audio_path=xxx&prompt_lang=zh
```

---

## GET /set_refer_audio — 预设参考音频

设置后，后续 `/tts` 调用可以不再传 [ref_audio_path](file:///e:/workspace/yiluomu/tts/GPT-SoVITS/GPT_SoVITS/TTS_infer_pack/TTS.py#762-764)。

```http
GET http://127.0.0.1:9880/set_refer_audio?refer_audio_path=e:/你的路径/参考音频.wav
```

**响应**：`{"message": "success"}`

```python
requests.get("http://127.0.0.1:9880/set_refer_audio", params={
    "refer_audio_path": r"e:/workspace/yiluomu/tts/v4/八重樱/reference_audios/中文/emotions/【默认】这个身体似乎不会老去，但我想见的人，却都离去了。.wav"
})
```

---

## GET /set_gpt_weights — 切换 GPT 模型

热切换到其他角色的 GPT 模型，无需重启服务：

```http
GET http://127.0.0.1:9880/set_gpt_weights?weights_path=e:/你的路径/角色名-eXX.ckpt
```

**响应**：`{"message": "success"}`

---

## GET /set_sovits_weights — 切换 SoVITS 模型

热切换到其他角色的 SoVITS 模型：

```http
GET http://127.0.0.1:9880/set_sovits_weights?weights_path=e:/你的路径/角色名_eXX_sXXX_lXX.pth
```

**响应**：`{"message": "success"}`

---

## GET /control — 控制服务

```http
GET http://127.0.0.1:9880/control?command=restart
GET http://127.0.0.1:9880/control?command=exit
```

| command | 效果 |
|---------|------|
| `restart` | 重新加载模型并重启服务 |
| `exit` | 停止服务进程 |

---

## 在 Sakura 后端集成的推荐写法

```python
# tts_service.py
import requests
from pathlib import Path

TTS_BASE_URL = "http://127.0.0.1:9880"
REF_AUDIO = r"e:/workspace/yiluomu/tts/v4/八重樱/reference_audios/中文/emotions/【默认】这个身体似乎不会老去，但我想见的人，却都离去了。.wav"
REF_TEXT = "这个身体似乎不会老去，但我想见的人，却都离去了。"

def synthesize_speech(text: str) -> bytes | None:
    """
    将文字合成为语音，返回 wav 二进制。失败返回 None。
    """
    try:
        resp = requests.post(
            f"{TTS_BASE_URL}/tts",
            json={
                "text": text,
                "text_lang": "zh",
                "ref_audio_path": REF_AUDIO,
                "prompt_text": REF_TEXT,
                "prompt_lang": "zh",
                "media_type": "wav",
                "streaming_mode": False,
                "speed_factor": 1.0,
            },
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.content
        print(f"[TTS] 合成失败: {resp.json()}")
        return None
    except requests.exceptions.ConnectionError:
        print("[TTS] GPT-SoVITS 服务未启动，请先运行 api_v2.py")
        return None
    except requests.exceptions.Timeout:
        print("[TTS] 合成超时，文本过长或服务繁忙")
        return None
```

---

## 注意事项

| 事项 | 说明 |
|------|------|
| [ref_audio_path](file:///e:/workspace/yiluomu/tts/GPT-SoVITS/GPT_SoVITS/TTS_infer_pack/TTS.py#762-764) 必须是绝对路径 | 相对路径会报 400 错误 |
| 参考音频须为 3~10 秒 | 过短或过长都会报错 |
| 首次请求较慢 | 模型第一次推理需要预热，后续请求更快 |
| 服务不支持并发 | 同时只能处理一个 TTS 请求（workers=1） |
| CORS | 默认未配置跨域，前端直接调用需在 api_v2.py 中加 CORSMiddleware |
