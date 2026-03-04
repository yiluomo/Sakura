"""
tts/engines/fish_audio.py
Fish Audio TTS 引擎实现。

API 文档：https://fish.audio/zh-CN/
接口：POST https://api.fish.audio/v1/tts
"""

import httpx
from tts.base import BaseTTSEngine
from config import FISH_AUDIO_API_KEY, FISH_AUDIO_MODEL_ID

_API_URL = "https://api.fish.audio/v1/tts"


class FishAudioEngine(BaseTTSEngine):

    async def synthesize(self, text: str) -> bytes:
        """
        调用 Fish Audio API 将文本合成为 MP3 音频。

        Args:
            text: 要合成的文本

        Returns:
            MP3 格式音频的二进制数据

        Raises:
            httpx.HTTPStatusError: API 请求失败
            Exception: 其他错误
        """
        headers = {
            "Authorization": f"Bearer {FISH_AUDIO_API_KEY}",
            "Content-Type":  "application/json",
        }

        payload = {
            "reference_id": FISH_AUDIO_MODEL_ID,
            "text":         text,
            "format":       "mp3",
            "mp3_bitrate":  128,
            "latency":      "balanced",   # "normal" 更稳定；"balanced" 延迟更低
            "normalize":    True,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            return response.content
