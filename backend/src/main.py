import sys
import io

# 强制设置标准输出为 UTF-8，解决 Windows 下重定向到文件时的编码错误
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat import router as chat_router
from db.database import init_db

# 定义异步生命周期函数（核心替换 on_event 的部分）
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理
    yield 前：服务启动时执行（原 startup 逻辑）
    yield 后：服务关闭时执行（如需 shutdown 逻辑，加在这里即可）
    """
    # 原有启动逻辑：异步初始化数据库
    await init_db()
    print("[INFO] 数据库初始化完成")
    yield  # 分割线，启动完成，开始处理请求
    # 如需服务关闭逻辑，写在这里（比如关闭数据库连接池、清理资源）
    # 示例：await close_db()
    # print("[INFO] 服务关闭，资源清理完成")

# 初始化app时绑定lifespan
app = FastAPI(title="樱", lifespan=lifespan)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境替换为具体前端域名，如["http://localhost:8080"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册聊天路由
app.include_router(chat_router, prefix="/api")

# 根路径接口
@app.get("/")
async def root():
    return {"msg": "你好"}

# 新增：PyCharm直接启动FastAPI服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发模式自动重载
    )