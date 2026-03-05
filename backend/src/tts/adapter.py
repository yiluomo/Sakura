"""
tts/adapter.py
TTS 统一调度器。

职责：
  - 根据 config.TTS_ENGINE 实例化对应引擎（工厂模式）
  - 调用引擎生成音频，保存到 audio_cache/ 目录
  - 文件名基于文本 MD5，相同文字命中缓存直接返回（不重复调用 API）
  - 缓存文件超过上限时，自动删除最旧的文件
  - 透传 GPT-SoVITS 管理接口（set_refer_audio / switch_weights）

对外暴露的函数：
    await tts_adapter.synthesize(text)                    → "/audio/xxxx.wav" 或 None
    await tts_adapter.set_refer_audio(refer_audio_path)   → bool（仅 gpt_sovits 引擎）
    await tts_adapter.switch_gpt_weights(weights_path)    → bool（仅 gpt_sovits 引擎）
    await tts_adapter.switch_sovits_weights(weights_path) → bool（仅 gpt_sovits 引擎）
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
    if TTS_ENGINE == "gpt_sovits":
        from tts.engines.gpt_sovits import GptSoVitsEngine
        return GptSoVitsEngine()
    # 在此处添加新引擎：
    # elif TTS_ENGINE == "edge_tts":
    #     from tts.engines.edge_tts import EdgeTTSEngine
    #     return EdgeTTSEngine()
    raise ValueError(f"未知的 TTS 引擎：{TTS_ENGINE}，请检查 config.TTS_ENGINE")


# 引擎输出格式对应的文件扩展名（缓存文件后缀与音频格式一致）
_ENGINE_EXT = {
    "gpt_sovits": ".wav",
}


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
        """将文本哈希为唯一文件名，后缀按当前引擎类型决定。"""
        md5 = hashlib.md5(text.encode("utf-8")).hexdigest()
        ext = _ENGINE_EXT.get(TTS_ENGINE, ".mp3")
        return f"{md5}{ext}"

    @staticmethod
    def _cleanup_cache():
        """缓存文件数量超过上限时，删除最旧的文件（兼容所有引擎缓存格式）。"""
        files = sorted(
            [
                p for ext in _ENGINE_EXT.values()
                for p in AUDIO_CACHE_DIR.glob(f"*{ext}")
            ],
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
            "/audio/{filename}" 或 None（TTS 未启用 / 合成失败）
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

    # ─────────────────────────────────────────────────────────
    # GPT-SoVITS 管理接口透传（仅 gpt_sovits 引擎可用）
    # ─────────────────────────────────────────────────────────

    async def set_refer_audio(self, refer_audio_path: str) -> bool:
        """
        预设参考音频路径（透传至 GPT-SoVITS GET /set_refer_audio）。
        设置后，后续 /tts 调用可不再传 ref_audio_path。

        Returns:
            True 表示成功，False 表示引擎不支持或请求失败
        """
        engine = self._get_engine()
        if hasattr(engine, "set_refer_audio"):
            return await engine.set_refer_audio(refer_audio_path)
        print(f"⚠️  [TTS] 当前引擎 ({TTS_ENGINE}) 不支持 set_refer_audio")
        return False

    async def switch_gpt_weights(self, weights_path: str) -> bool:
        """
        热切换 GPT 模型权重（透传至 GPT-SoVITS GET /set_gpt_weights）。
        无需重启服务即可切换角色。

        Returns:
            True 表示成功，False 表示引擎不支持或请求失败
        """
        engine = self._get_engine()
        if hasattr(engine, "switch_gpt_weights"):
            return await engine.switch_gpt_weights(weights_path)
        print(f"⚠️  [TTS] 当前引擎 ({TTS_ENGINE}) 不支持 switch_gpt_weights")
        return False

    async def switch_sovits_weights(self, weights_path: str) -> bool:
        """
        热切换 SoVITS 模型权重（透传至 GPT-SoVITS GET /set_sovits_weights）。
        无需重启服务即可切换角色。

        Returns:
            True 表示成功，False 表示引擎不支持或请求失败
        """
        engine = self._get_engine()
        if hasattr(engine, "switch_sovits_weights"):
            return await engine.switch_sovits_weights(weights_path)
        print(f"⚠️  [TTS] 当前引擎 ({TTS_ENGINE}) 不支持 switch_sovits_weights")
        return False


# 全局单例
tts_adapter = TTSAdapter()
