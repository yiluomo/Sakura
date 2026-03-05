"""
tts/engines/gpt_sovits.py
GPT-SoVITS 本地 TTS 引擎实现。

API 文档：GPT-SoVITS_API文档.md
接口：POST http://{host}:{port}/tts

启动服务（在 GPT-SoVITS 目录下执行）：
    .\\runtime\\python.exe api_v2.py -a 127.0.0.1 -p 9880

支持的接口：
  POST /tts              — 文本转语音（主接口）
  GET  /set_refer_audio  — 预设参考音频（设置后 /tts 无需重复传 ref_audio_path）
  GET  /set_gpt_weights  — 热切换 GPT 模型权重
  GET  /set_sovits_weights — 热切换 SoVITS 模型权重

注意：
  - ref_audio_path 必须是 API 服务器端可访问的本地绝对路径
  - 切换角色时调用一次 set_gpt_weights / set_sovits_weights 即可
  - 推荐填写 prompt_text（参考音频对应台词），可提升音色稳定性
  - 服务不支持并发，同时只能处理一个 TTS 请求（workers=1）
"""

import httpx
from typing import Optional
from tts.base import BaseTTSEngine
from config import (
    GPT_SOVITS_BASE_URL,
    GPT_SOVITS_REF_AUDIO_PATH,
    GPT_SOVITS_PROMPT_TEXT,
    GPT_SOVITS_PROMPT_LANG,
    GPT_SOVITS_TEXT_LANG,
    GPT_SOVITS_SPEED_FACTOR,
    GPT_SOVITS_MEDIA_TYPE,
    GPT_SOVITS_TOP_K,
    GPT_SOVITS_TOP_P,
    GPT_SOVITS_TEMPERATURE,
    GPT_SOVITS_SEED,
    GPT_SOVITS_BATCH_SIZE,
    GPT_SOVITS_SAMPLE_STEPS,
    GPT_SOVITS_TIMEOUT,
    GPT_SOVITS_GPT_WEIGHTS,
    GPT_SOVITS_SOVITS_WEIGHTS,
)


class GptSoVitsEngine(BaseTTSEngine):
    """
    GPT-SoVITS 本地推理引擎。

    本引擎直连本地运行的 api_v2.py 服务，无需联网。
    通过 config.TTS_ENGINE = "gpt_sovits" 启用。

    API 参数全部对齐官方文档（POST /tts）：
      text, text_lang, ref_audio_path, prompt_lang, prompt_text,
      media_type, streaming_mode, speed_factor,
      top_k, top_p, temperature, seed, batch_size, sample_steps
    """

    # 当前已加载的模型权重路径（类级缓存，避免每次请求都重复切换）
    _loaded_gpt_weights: Optional[str] = None
    _loaded_sovits_weights: Optional[str] = None

    async def _ensure_weights_loaded(self, client: httpx.AsyncClient) -> None:
        """
        按需切换 GPT / SoVITS 模型权重。
        仅在配置了权重路径且尚未加载（或与当前已加载路径不同）时才发请求。

        API: GET /set_gpt_weights?weights_path=xxx
             GET /set_sovits_weights?weights_path=xxx
        """
        if GPT_SOVITS_GPT_WEIGHTS and GPT_SOVITS_GPT_WEIGHTS != self.__class__._loaded_gpt_weights:
            resp = await client.get(
                f"{GPT_SOVITS_BASE_URL}/set_gpt_weights",
                params={"weights_path": GPT_SOVITS_GPT_WEIGHTS},
                timeout=15.0,
            )
            resp.raise_for_status()
            self.__class__._loaded_gpt_weights = GPT_SOVITS_GPT_WEIGHTS
            print(f"🔄 [GPT-SoVITS] GPT 模型已切换：{GPT_SOVITS_GPT_WEIGHTS}")

        if GPT_SOVITS_SOVITS_WEIGHTS and GPT_SOVITS_SOVITS_WEIGHTS != self.__class__._loaded_sovits_weights:
            resp = await client.get(
                f"{GPT_SOVITS_BASE_URL}/set_sovits_weights",
                params={"weights_path": GPT_SOVITS_SOVITS_WEIGHTS},
                timeout=15.0,
            )
            resp.raise_for_status()
            self.__class__._loaded_sovits_weights = GPT_SOVITS_SOVITS_WEIGHTS
            print(f"🔄 [GPT-SoVITS] SoVITS 模型已切换：{GPT_SOVITS_SOVITS_WEIGHTS}")

    async def set_refer_audio(self, refer_audio_path: str) -> bool:
        """
        预设参考音频，设置后后续 /tts 调用可不再传 ref_audio_path。

        API: GET /set_refer_audio?refer_audio_path=xxx
        Returns:
            True 表示设置成功，False 表示失败
        """
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            try:
                resp = await client.get(
                    f"{GPT_SOVITS_BASE_URL}/set_refer_audio",
                    params={"refer_audio_path": refer_audio_path},
                )
                resp.raise_for_status()
                print(f"✅ [GPT-SoVITS] 参考音频已预设：{refer_audio_path}")
                return True
            except Exception as e:
                print(f"❌ [GPT-SoVITS] 预设参考音频失败：{e}")
                return False

    async def switch_gpt_weights(self, weights_path: str) -> bool:
        """
        热切换 GPT 模型权重。

        API: GET /set_gpt_weights?weights_path=xxx
        """
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            try:
                resp = await client.get(
                    f"{GPT_SOVITS_BASE_URL}/set_gpt_weights",
                    params={"weights_path": weights_path},
                )
                resp.raise_for_status()
                self.__class__._loaded_gpt_weights = weights_path
                print(f"✅ [GPT-SoVITS] GPT 模型已切换：{weights_path}")
                return True
            except Exception as e:
                print(f"❌ [GPT-SoVITS] GPT 模型切换失败：{e}")
                return False

    async def switch_sovits_weights(self, weights_path: str) -> bool:
        """
        热切换 SoVITS 模型权重。

        API: GET /set_sovits_weights?weights_path=xxx
        """
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            try:
                resp = await client.get(
                    f"{GPT_SOVITS_BASE_URL}/set_sovits_weights",
                    params={"weights_path": weights_path},
                )
                resp.raise_for_status()
                self.__class__._loaded_sovits_weights = weights_path
                print(f"✅ [GPT-SoVITS] SoVITS 模型已切换：{weights_path}")
                return True
            except Exception as e:
                print(f"❌ [GPT-SoVITS] SoVITS 模型切换失败：{e}")
                return False

    async def synthesize(self, text: str) -> bytes:
        """
        调用本地 GPT-SoVITS POST /tts 接口将文本合成为音频。

        请求参数严格对齐 API 文档（GPT-SoVITS_API文档.md）：
          必填：text, text_lang, ref_audio_path, prompt_lang
          选填：prompt_text, media_type, streaming_mode, speed_factor,
               top_k, top_p, temperature, seed, batch_size, sample_steps

        Args:
            text: 要合成的文本

        Returns:
            音频二进制数据（格式由 GPT_SOVITS_MEDIA_TYPE 决定，默认 wav）

        Raises:
            httpx.ConnectError: GPT-SoVITS 服务未启动
            RuntimeError: API 返回非 200 状态（含错误详情）
        """
        payload = {
            # ── 必填参数 ──────────────────────────────────────
            "text":           text,
            "text_lang":      GPT_SOVITS_TEXT_LANG,
            "ref_audio_path": GPT_SOVITS_REF_AUDIO_PATH,
            "prompt_lang":    GPT_SOVITS_PROMPT_LANG,
            # ── 选填参数（对齐 API 文档默认值） ────────────────
            "prompt_text":    GPT_SOVITS_PROMPT_TEXT,
            "media_type":     GPT_SOVITS_MEDIA_TYPE,
            "streaming_mode": False,          # 等待完整音频后一次性返回（推荐）
            "speed_factor":   GPT_SOVITS_SPEED_FACTOR,
            "top_k":          GPT_SOVITS_TOP_K,
            "top_p":          GPT_SOVITS_TOP_P,
            "temperature":    GPT_SOVITS_TEMPERATURE,
            "seed":           GPT_SOVITS_SEED,           # -1 = 随机，固定值 = 可复现
            "batch_size":     GPT_SOVITS_BATCH_SIZE,
            "sample_steps":   GPT_SOVITS_SAMPLE_STEPS,  # V4 模型专用，越高质量越好但越慢
        }

        # 禁用 proxies 防止本地 127.0.0.1 的请求被 VPN 或 Clash 拦截导致 502 Bad Gateway
        async with httpx.AsyncClient(timeout=GPT_SOVITS_TIMEOUT, trust_env=False) as client:
            # 1. 确保模型权重已加载（只在配置了权重路径时才请求）
            await self._ensure_weights_loaded(client)

            # 2. 发起 TTS 合成请求
            response = await client.post(
                f"{GPT_SOVITS_BASE_URL}/tts",
                json=payload,
            )

            if response.status_code != 200:
                # API 返回 400 时附带 JSON 错误信息，一并抛出
                try:
                    err = response.json()
                    raise RuntimeError(
                        f"GPT-SoVITS 合成失败 [{response.status_code}]："
                        f"{err.get('message', '')} | {err.get('Exception', '')}"
                    )
                except Exception as parse_err:
                    response.raise_for_status()
                    raise parse_err

            return response.content
