"""
main.py - LiteKB API Server
"""
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
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

# ==================== 数据模型 ====================

class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
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

# ==================== 初始化 ====================

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库
    from app.db.json_store import json_store
    os.makedirs("./data", exist_ok=True)
    
    # 初始化向量库
    from app.services.vector import vector_store
    try:
        await vector_store.create_collection()
    except Exception as e:
        print(f"向量库初始化: {e}")
    
    # 初始化缓存
    from app.services.cache import cache
    await cache.get_redis()
    
    yield
    # 关闭时清理
    await cache.close()

app = FastAPI(
    title="LiteKB API",
    description="轻量级开源知识库系统 API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 缓存中间件
@app.middleware("http")
async def cache_middleware(request: Request, call_next):
    # 简单缓存：对 GET 请求缓存 10 秒
    if request.method == "GET" and request.url.path.startswith("/api/v1/kb/"):
        from app.services.cache import cache
        cache_key = f"http:{request.url.path}:{dict(request.query_params)}"
        cached = await cache.get(cache_key)
        if cached:
            from fastapi.responses import JSONResponse
            return JSONResponse(content=cached)
        
        response = await call_next(request)
        
        # 缓存响应
        if response.status_code == 200:
            try:
                body = b"".join([chunk async for chunk in response.body_iterator])
                await cache.set(cache_key, json.loads(body), 10)
                return JSONResponse(content=json.loads(body))
            except:
                pass
        
        return response
    
    return await call_next(request)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==================== 辅助函数 ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ==================== 数据库 ====================

from app.db.json_store import json_store

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
    
    user_data = json_store.get_user(user_id)
    if user_data is None:
        raise credentials_exception
    
    return User(**user_data)

# ==================== API 路由 ====================

@app.get("/")
async def root():
    return {"message": "LiteKB API", "version": "0.1.0"}

@app.post("/api/v1/auth/register", response_model=User)
async def register(user: UserCreate):
    """用户注册"""
    existing = json_store.get_user_by_username(user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed = pwd_context.hash(user.password)
    user_data = {
        "id": str(uuid.uuid4()),
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed,
    }
    return User(**json_store.create_user(user_data["id"], user_data))

@app.post("/api/v1/auth/login", response_model=Token)
async def login(user: UserLogin):
    """用户登录"""
    existing = json_store.get_user_by_username(user.username)
    if not existing or not verify_password(user.password, existing.get("hashed_password", "")):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": existing["id"]})
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
        "id": str(uuid.uuid4()),
        "name": kb.name,
        "description": kb.description,
        "created_by": current_user.id,
    }
    return KnowledgeBase(**json_store.create_kb(kb_data["id"], kb_data))

@app.get("/api/v1/kb", response_model=List[KnowledgeBase])
async def list_kbs(current_user: User = Depends(get_current_user)):
    """列出知识库"""
    return [KnowledgeBase(**kb) for kb in json_store.list_kbs()]

@app.get("/api/v1/kb/{kb_id}", response_model=KnowledgeBase)
async def get_kb(kb_id: str, current_user: User = Depends(get_current_user)):
    """获取知识库"""
    kb = json_store.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return KnowledgeBase(**kb)

@app.delete("/api/v1/kb/{kb_id}")
async def delete_kb(kb_id: str, current_user: User = Depends(get_current_user)):
    """删除知识库"""
    if not json_store.delete_kb(kb_id):
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return {"message": "deleted"}

# ==================== 文档 API ====================

@app.post("/api/v1/kb/{kb_id}/docs", response_model=Document)
async def create_doc(kb_id: str, doc: DocumentCreate, current_user: User = Depends(get_current_user)):
    """创建文档"""
    kb = json_store.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    doc_data = {
        "id": str(uuid.uuid4()),
        "kb_id": kb_id,
        "title": doc.title,
        "content": doc.content,
        "metadata": doc.metadata,
    }
    return Document(**json_store.create_doc(doc_data["id"], doc_data))

@app.get("/api/v1/kb/{kb_id}/docs", response_model=List[Document])
async def list_documents(kb_id: str, skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user)):
    """列出文档"""
    return [Document(**d) for d in json_store.list_docs(kb_id, skip, limit)]

@app.delete("/api/v1/kb/{kb_id}/docs/{doc_id}")
async def delete_document(kb_id: str, doc_id: str, current_user: User = Depends(get_current_user)):
    """删除文档"""
    if not json_store.delete_doc(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "deleted"}

# ==================== 搜索 API ====================

@app.post("/api/v1/kb/{kb_id}/search")
async def search_kb(kb_id: str, request: SearchRequest, current_user: User = Depends(get_current_user)):
    """知识库内搜索"""
    kb = json_store.get_kb(kb_id)
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
    for kb in json_store.list_kbs():
        kb_id = kb["id"]
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
                "kb_name": kb.get("name", ""),
            })
    
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return {
        "results": all_results[:request.top_k * 3],
        "total_kbs": len(json_store.list_kbs()),
        "strategy": request.strategy
    }

# ==================== RAG 对话 API ====================

@app.post("/api/v1/kb/{kb_id}/chat")
async def chat_with_kb(kb_id: str, chat: ChatRequest, current_user: User = Depends(get_current_user)):
    """RAG 对话"""
    kb = json_store.get_kb(kb_id)
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
    kb = json_store.get_kb(kb_id)
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
    kb = json_store.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    from app.services.graph import graph_service
    return graph_service.get_graph(kb_id)

@app.post("/api/v1/kb/{kb_id}/graph/build")
async def build_graph(kb_id: str, rebuild: bool = False, current_user: User = Depends(get_current_user)):
    """构建知识图谱"""
    kb = json_store.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    from app.services.graph import graph_service
    
    docs = json_store.list_docs(kb_id)
    stats = {"entities": 0, "relations": 0}
    
    for doc in docs:
        if doc.get("content"):
            result = await graph_service.build_graph(
                kb_id=kb_id,
                doc_id=doc["id"],
                text=doc["content"][:5000]
            )
            stats["entities"] += result.get("entities", 0)
            stats["relations"] += result.get("relations", 0)
    
    return {"message": "图谱构建完成", **stats}

# ==================== 注册其他路由 ====================

# 模型管理
try:
    from app.api.models import router as models_router
    app.include_router(models_router, prefix="")
    print("✅ 模型管理 API 已注册")
except Exception as e:
    print(f"⚠️ 模型管理 API 注册失败: {e}")

# 统计 API
try:
    from app.api.stats import router as stats_router
    app.include_router(stats_router, prefix="")
    print("✅ 统计 API 已注册")
except Exception as e:
    print(f"⚠️ 统计 API 注册失败: {e}")

# 分享 API
try:
    from app.api.share import router as share_router
    app.include_router(share_router, prefix="")
    print("✅ 分享 API 已注册")
except Exception as e:
    print(f"⚠️ 分享 API 注册失败: {e}")

# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
