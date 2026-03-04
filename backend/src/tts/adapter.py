"""
tts/adapter.py
TTS 统一调度器。

职责：
  - 根据 config.TTS_ENGINE 实例化对应引擎（工厂模式）
  - 调用引擎生成音频，保存到 audio_cache/ 目录
  - 文件名基于文本 MD5，相同文字命中缓存直接返回（不重复调用 API）
  - 缓存文件超过上限时，自动删除最旧的文件

对外只暴露一个函数：
    await tts_adapter.synthesize(text)  → "/audio/xxxx.mp3" 或 None
"""

import asyncio
import hashlib
from pathlib import Path
from typing import Optional

import aiofiles

from config import (
    TTS_ENABLED, TTS_ENGINE,
    AUDIO_CACHE_DIR, AUDIO_CACHE_MAX_FILES,
)


# ─────────────────────────────────────────────────────────────
# 引擎工厂
# ─────────────────────────────────────────────────────────────

def _create_engine():
    """根据 TTS_ENGINE 配置创建对应的引擎实例。"""
    if TTS_ENGINE == "fish_audio":
        from tts.engines.fish_audio import FishAudioEngine
        return FishAudioEngine()
    # 在此处添加新引擎：
    # elif TTS_ENGINE == "edge_tts":
    #     from tts.engines.edge_tts import EdgeTTSEngine
    #     return EdgeTTSEngine()
    raise ValueError(f"未知的 TTS 引擎：{TTS_ENGINE}，请检查 config.TTS_ENGINE")


# ─────────────────────────────────────────────────────────────
# TTS 调度器
# ─────────────────────────────────────────────────────────────

class TTSAdapter:

    def __init__(self):
        self._engine = None
        self._lock = asyncio.Lock()

    def _get_engine(self):
        """延迟初始化引擎（首次调用时创建）。"""
        if self._engine is None:
            self._engine = _create_engine()
        return self._engine

    @staticmethod
    def _text_to_filename(text: str) -> str:
        """将文本哈希为唯一文件名，避免路径字符问题。"""
        md5 = hashlib.md5(text.encode("utf-8")).hexdigest()
        return f"{md5}.mp3"

    @staticmethod
    def _cleanup_cache():
        """缓存文件数量超过上限时，删除最旧的文件。"""
        files = sorted(
            AUDIO_CACHE_DIR.glob("*.mp3"),
            key=lambda p: p.stat().st_mtime
        )
        while len(files) > AUDIO_CACHE_MAX_FILES:
            oldest = files.pop(0)
            try:
                oldest.unlink()
                print(f"🗑️  [TTS] 清理旧缓存：{oldest.name}")
            except Exception:
                pass

    async def synthesize(self, text: str) -> Optional[str]:
        """
        将文本合成为音频，返回前端可访问的 URL 路径。

        Args:
            text: 要合成的文本内容

        Returns:
            "/audio/{filename}.mp3" 或 None（TTS 未启用 / 合成失败）
        """
        if not TTS_ENABLED or not text or not text.strip():
            return None

        AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        filename = self._text_to_filename(text)
        filepath = AUDIO_CACHE_DIR / filename

        # 缓存命中 → 直接返回
        if filepath.exists():
            print(f"✅ [TTS] 缓存命中：{filename}")
            return f"/audio/{filename}"

        # 未命中 → 调用引擎合成（加锁防止同一文本并发重复请求）
        async with self._lock:
            # 再次检查（可能在等锁期间已经生成）
            if filepath.exists():
                return f"/audio/{filename}"

            try:
                engine = self._get_engine()
                audio_data = await engine.synthesize(text)

                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(audio_data)

                print(f"✅ [TTS] 音频已生成：{filename}（{len(audio_data)} bytes）")

                # 异步清理旧缓存（不阻塞当前请求）
                asyncio.create_task(
                    asyncio.to_thread(self._cleanup_cache)
                )

                return f"/audio/{filename}"

            except Exception as e:
                print(f"❌ [TTS] 合成失败：{e}")
                return None


# 全局单例
tts_adapter = TTSAdapter()
