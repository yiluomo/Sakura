from fastapi import APIRouter, Depends
from api.deps import verify_token
from pydantic import BaseModel
from tts import tts_adapter

router = APIRouter(dependencies=[Depends(verify_token)])


class TTSRequest(BaseModel):
    text: str


class TTSSetReferAudioRequest(BaseModel):
    """预设参考音频（对应 GPT-SoVITS GET /set_refer_audio）"""
    refer_audio_path: str  # 服务器端绝对路径，3~10 秒音频


class TTSSwitchWeightsRequest(BaseModel):
    """热切换模型权重（对应 GPT-SoVITS GET /set_gpt_weights / /set_sovits_weights）"""
    weights_path: str  # .ckpt（GPT）或 .pth（SoVITS）的绝对/相对路径


@router.post("/tts")
async def generate_tts(req: TTSRequest):
    """
    按需生成 TTS 音频。
    前端手动点击播放按钮且尚未生成过音频时调用。
    生命周期内命中缓存时直接返回已有 URL，不重复请求 GPT-SoVITS API。
    """
    try:
        audio_url = await tts_adapter.synthesize(req.text)
        return {"audio_url": audio_url}
    except Exception as e:
        # 返回友好的错误信息，不暴露技术细节
        error_msg = "TTS 服务不可用"
        if "Connection" in str(e) or "connect" in str(e).lower():
            error_msg = "TTS 服务未启动"
        return {"audio_url": None, "error": error_msg}


@router.post("/tts/set_refer_audio")
async def tts_set_refer_audio(req: TTSSetReferAudioRequest):
    """
    预设参考音频路径（透传至 GPT-SoVITS GET /set_refer_audio）。
    设置成功后，后续 TTS 合成请求无需重复传递 ref_audio_path。
    """
    success = await tts_adapter.set_refer_audio(req.refer_audio_path)
    if success:
        return {"status": "ok", "msg": f"参考音频已预设：{req.refer_audio_path}"}
    return {"status": "error", "msg": "预设参考音频失败，请检查服务是否运行及路径是否正确"}


@router.post("/tts/set_gpt_weights")
async def tts_set_gpt_weights(req: TTSSwitchWeightsRequest):
    """
    热切换 GPT 模型权重（透传至 GPT-SoVITS GET /set_gpt_weights）。
    无需重启服务，直接切换为其他角色的 GPT 模型（.ckpt 文件）。
    """
    success = await tts_adapter.switch_gpt_weights(req.weights_path)
    if success:
        return {"status": "ok", "msg": f"GPT 模型已切换：{req.weights_path}"}
    return {"status": "error", "msg": "GPT 模型切换失败，请检查服务是否运行及路径是否正确"}


@router.post("/tts/set_sovits_weights")
async def tts_set_sovits_weights(req: TTSSwitchWeightsRequest):
    """
    热切换 SoVITS 模型权重（透传至 GPT-SoVITS GET /set_sovits_weights）。
    无需重启服务，直接切换为其他角色的 SoVITS 模型（.pth 文件）。
    """
    success = await tts_adapter.switch_sovits_weights(req.weights_path)
    if success:
        return {"status": "ok", "msg": f"SoVITS 模型已切换：{req.weights_path}"}
    return {"status": "error", "msg": "SoVITS 模型切换失败，请检查服务是否运行及路径是否正确"}
