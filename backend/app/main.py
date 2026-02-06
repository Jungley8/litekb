"""
main.py - LiteKB API Server (生产优化版)
"""
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, AsyncGenerator
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import uuid
import os
import json

# ==================== 配置 ====================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ==================== 初始化中间件 ====================

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库
    from app.db.factory import db
    from app.db.pool import init_db_pool
    
    os.makedirs("./data", exist_ok=True)
    init_db_pool()
    
    # 初始化向量库
    from app.services.vector import vector_store
    try:
        await vector_store.create_collection()
    except Exception as e:
        print(f"向量库初始化: {e}")
    
    # 初始化缓存
    from app.services.cache import cache
    await cache.get_redis()
    
    # 初始化 Sentry
    from app.sentry import setup_sentry
    setup_sentry()
    
    yield
    # 关闭时清理
    pass


app = FastAPI(
    title="LiteKB API",
    description="轻量级开源知识库系统 API",
    version="1.0.0",
    lifespan=lifespan,
    debug=DEBUG,
)

# ==================== 添加安全中间件 ====================

# CORS (需要在最开始)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
from app.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(
    RateLimitMiddleware,
    calls=100,
    period=60
)

# Tracing 中间件 (自动追踪 API 请求)
from app.tracing.middleware import TracingMiddleware
app.add_middleware(TracingMiddleware)

# Helmet Headers (非调试模式)
if not DEBUG:
    from app.middleware.helmet import HelmetMiddleware, HSTSMiddleware
    app.add_middleware(HelmetMiddleware)
    app.add_middleware(HSTSMiddleware, max_age=31536000)

# ==================== 数据模型 (增强验证) ====================

class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str

class User(BaseModel):
    id: str
    username: str
    email: Optional[str]
    created_at: datetime

class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None

class KnowledgeBase(BaseModel):
    id: str
    name: str
    description: Optional[str]
    doc_count: int
    created_at: datetime

class DocumentCreate(BaseModel):
    title: str
    content: Optional[str] = None
    metadata: Optional[dict] = None

class Document(BaseModel):
    id: str
    title: str
    content: Optional[str]
    status: str
    created_at: datetime

class ChatRequest(BaseModel):
    kb_id: str
    message: str
    history: Optional[List[dict]] = []
    mode: str = "naive"

class SearchRequest(BaseModel):
    query: str
    strategy: str = "hybrid"
    top_k: int = 10
    filters: Optional[dict] = None

# ==================== 数据库 ====================

from app.db.factory import db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==================== 辅助函数 ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ==================== 认证依赖 ====================

async def get_current_user(token: str) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_data = db.get_user(user_id)
    if user_data is None:
        raise credentials_exception
    
    return User(**user_data.__dict__ if hasattr(user_data, '__dict__') else user_data)

# ==================== API 路由 ====================

@app.get("/")
async def root():
    return {"message": "LiteKB API", "version": "1.0.0"}

@app.post("/api/v1/auth/register", response_model=User)
async def register(user: UserCreate):
    """用户注册"""
    existing = db.get_user_by_username(user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed = pwd_context.hash(user.password)
    user_data = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed,
    }
    return db.create_user(str(uuid.uuid4()), user_data)

@app.post("/api/v1/auth/login", response_model=Token)
async def login(user: UserLogin):
    """用户登录"""
    existing = db.get_user_by_username(user.username)
    if not existing or not verify_password(user.password, existing.hashed_password if hasattr(existing, 'hashed_password') else existing.get('hashed_password', '')):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": existing.id if hasattr(existing, 'id') else existing['id']})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/v1/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户"""
    return current_user

# ==================== 知识库 API ====================

@app.post("/api/v1/kb", response_model=KnowledgeBase)
async def create_kb(kb: KnowledgeBaseCreate, current_user: User = Depends(get_current_user)):
    """创建知识库"""
    kb_data = {
        "name": kb.name,
        "description": kb.description,
        "created_by": current_user.id if hasattr(current_user, 'id') else current_user['id'],
    }
    return db.create_kb(str(uuid.uuid4()), kb_data)

@app.get("/api/v1/kb", response_model=List[KnowledgeBase])
async def list_kbs(current_user: User = Depends(get_current_user)):
    """列出知识库"""
    return db.list_kbs()

@app.get("/api/v1/kb/{kb_id}", response_model=KnowledgeBase)
async def get_kb(kb_id: str, current_user: User = Depends(get_current_user)):
    """获取知识库"""
    kb = db.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb

@app.delete("/api/v1/kb/{kb_id}")
async def delete_kb(kb_id: str, current_user: User = Depends(get_current_user)):
    """删除知识库"""
    if not db.delete_kb(kb_id):
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return {"message": "deleted"}

# ==================== 文档 API ====================

@app.post("/api/v1/kb/{kb_id}/docs", response_model=Document)
async def create_doc(kb_id: str, doc: DocumentCreate, current_user: User = Depends(get_current_user)):
    """创建文档"""
    kb = db.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    doc_data = {
        "kb_id": kb_id,
        "title": doc.title,
        "content": doc.content,
        "metadata": doc.metadata,
    }
    return db.create_doc(str(uuid.uuid4()), doc_data)

@app.get("/api/v1/kb/{kb_id}/docs", response_model=List[Document])
async def list_documents(kb_id: str, skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user)):
    """列出文档"""
    return db.list_docs(kb_id, skip, limit)

@app.delete("/api/v1/kb/{kb_id}/docs/{doc_id}")
async def delete_document(kb_id: str, doc_id: str, current_user: User = Depends(get_current_user)):
    """删除文档"""
    if not db.delete_doc(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "deleted"}

# ==================== 搜索 API ====================

@app.post("/api/v1/kb/{kb_id}/search")
async def search_kb(kb_id: str, request: SearchRequest, current_user: User = Depends(get_current_user)):
    """知识库内搜索"""
    kb = db.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    from app.services.search import search_service
    
    results = await search_service.hybrid_search(
        query=request.query,
        kb_id=kb_id,
        strategy=request.strategy,
        top_k=request.top_k,
        filters=request.filters
    )
    
    return {
        "results": [
            {
                "id": r.get("id", ""),
                "title": r.get("title", ""),
                "content": r.get("content", "")[:500],
                "score": r.get("score", 0),
                "type": r.get("type", "document")
            }
            for r in results
        ],
        "strategy": request.strategy
    }

@app.post("/api/v1/search")
async def global_search(request: SearchRequest, current_user: User = Depends(get_current_user)):
    """全局搜索"""
    from app.services.search import search_service
    
    all_results = []
    for kb in db.list_kbs():
        kb_id = kb.id if hasattr(kb, 'id') else kb['id']
        results = await search_service.hybrid_search(
            query=request.query,
            kb_id=kb_id,
            strategy=request.strategy,
            top_k=request.top_k,
            filters=request.filters
        )
        for r in results:
            all_results.append({
                **r,
                "kb_id": kb_id,
                "kb_name": kb.name if hasattr(kb, 'name') else kb.get('name', ''),
            })
    
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return {
        "results": all_results[:request.top_k * 3],
        "total_kbs": len(db.list_kbs()),
        "strategy": request.strategy
    }

# ==================== RAG 对话 API ====================

@app.post("/api/v1/kb/{kb_id}/chat")
async def chat_with_kb(kb_id: str, chat: ChatRequest, current_user: User = Depends(get_current_user)):
    """RAG 对话"""
    kb = db.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    from app.services.rag import rag_engine
    
    response = await rag_engine.query(
        kb_id=kb_id,
        question=chat.message,
        mode=chat.mode,
        history=chat.history or []
    )
    
    return {
        "answer": response.answer,
        "sources": response.sources,
        "conversation_id": response.conversation_id
    }

@app.post("/api/v1/kb/{kb_id}/chat/stream")
async def stream_chat(kb_id: str, chat: ChatRequest, current_user: User = Depends(get_current_user)):
    """流式 RAG 对话 (SSE)"""
    kb = db.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    from app.services.sse import sse_service
    
    stream_id = str(uuid.uuid4())
    
    async def generate():
        async for chunk in sse_service.rag_stream(
            stream_id=stream_id,
            rag_engine=None,
            kb_id=kb_id,
            message=chat.message,
            mode=chat.mode,
        ):
            yield chunk
    
    return StreamingResponse(generate(), media_type="text/event-stream")

# ==================== 知识图谱 API ====================

@app.get("/api/v1/kb/{kb_id}/graph")
async def get_graph(kb_id: str, current_user: User = Depends(get_current_user)):
    """获取知识图谱"""
    kb = db.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    from app.services.graph import graph_service
    return graph_service.get_graph(kb_id)

@app.post("/api/v1/kb/{kb_id}/graph/build")
async def build_graph(kb_id: str, rebuild: bool = False, current_user: User = Depends(get_current_user)):
    """构建知识图谱"""
    kb = db.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    from app.services.graph import graph_service
    
    docs = db.list_docs(kb_id)
    stats = {"entities": 0, "relations": 0}
    
    for doc in docs:
        if doc.content:
            result = await graph_service.build_graph(
                kb_id=kb_id,
                doc_id=doc.id if hasattr(doc, 'id') else doc['id'],
                text=doc.content[:5000]
            )
            stats["entities"] += result.get("entities", 0)
            stats["relations"] += result.get("relations", 0)
    
    return {"message": "图谱构建完成", **stats}

# ==================== 注册其他路由 ====================

try:
    from app.api.models import router as models_router
    app.include_router(models_router, prefix="")
    print("✅ 模型管理 API 已注册")
except Exception as e:
    print(f"⚠️ 模型管理 API 注册失败: {e}")

try:
    from app.api.stats import router as stats_router
    app.include_router(stats_router, prefix="")
    print("✅ 统计 API 已注册")
except Exception as e:
    print(f"⚠️ 统计 API 注册失败: {e}")

try:
    from app.api.share import router as share_router
    app.include_router(share_router, prefix="")
    print("✅ 分享 API 已注册")


try:
    from app.api.tracing import router as tracing_router
    app.include_router(tracing_router, prefix="")
    print("✅ Tracing API 已注册")
except Exception as e:
    print(f"⚠️ Tracing API 注册失败: {e}")
except Exception as e:
    print(f"⚠️ 分享 API 注册失败: {e}")

# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    from app.services.cache import cache
    redis_status = "healthy"
    try:
        await cache.get_redis()
    except:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {
            "database": "healthy",
            "redis": redis_status,
            "qdrant": "healthy",
        }
    }

@app.get("/ready")
async def readiness_check():
    """就绪检查"""
    # 检查数据库
    try:
        with db.get_session() as session:
            session.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if "healthy" in db_status else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """应用指标"""
    try:
        user_count = len(db.list_users())
        kb_count = len(db.list_kbs())
    except:
        user_count = 0
        kb_count = 0
    
    from app.db.pool import pool_monitor
    pool_stats = pool_monitor.get_stats() if pool_monitor else {}
    
    return {
        "app_users_total": user_count,
        "app_kb_total": kb_count,
        "db_pool_size": pool_stats.get("pool_size", 0),
        "db_pool_checkedout": pool_stats.get("pool_checkedout", 0),
    }

# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        workers=4,
        loop="uvloop"
    )
