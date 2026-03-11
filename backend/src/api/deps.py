"""
api/deps.py ── FastAPI 通用依赖项
当前功能：静态 Token 认证
使用方式：在路由函数参数中添加  _: None = Depends(verify_token)
"""
from fastapi import Header, HTTPException, status
from config import API_TOKEN


async def verify_token(x_api_token: str = Header(..., alias="X-API-Token")) -> None:
    """
    验证请求头中的 X-API-Token。
    前端将 Token 硬编码后随每个请求一起发送，
    后端比对配置文件（或环境变量）中的值。
    """
    if x_api_token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 API Token",
        )
