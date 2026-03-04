"""
tts/base.py
TTS 引擎抽象基类。

换引擎时：继承 BaseTTSEngine，实现 synthesize() 方法即可。
adapter.py 无需修改，config.py 中改 TTS_ENGINE 一行即可切换。
"""

from abc import ABC, abstractmethod


class BaseTTSEngine(ABC):

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """
        将文本合成为音频二进制数据。

        Args:
            text: 要合成的文本内容

        Returns:
            音频二进制数据（MP3 格式）

        Raises:
            Exception: 合成失败时抛出异常
        """
        ...
