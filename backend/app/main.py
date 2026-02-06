from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import uuid
from contextlib import asynccontextmanager
import os

# ==================== 配置 ====================

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    from app.db import init_db
    from app.services.vector import vector_store
    
    init_db()
    
    # 初始化向量库集合
    try:
        vector_store.create_collection()
    except Exception as e:
        print(f"向量库初始化: {e}")
    
    yield
    # 关闭时清理
    pass

app = FastAPI(
    title="LiteKB API",
    description="轻量级开源知识库系统 API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None

class KnowledgeBase(BaseModel):
    id: str
    name: str
    description: Optional[str]
    doc_count: int
    created_at: datetime

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    kb_id: str
    message: str
    history: Optional[List[ChatMessage]] = []
    mode: str = "naive"

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    conversation_id: str

class SearchRequest(BaseModel):
    query: str
    strategy: str = "hybrid"
    top_k: int = 10
    filters: Optional[dict] = None

class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    score: float
    type: str

# ==================== 模拟数据库 ====================

users_db = {}
kb_db = {}
doc_db = {}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(username: str, password: str, email: Optional[str] = None) -> User:
    user_id = str(uuid.uuid4())
    hashed = pwd_context.hash(password)
    users_db[user_id] = {
        "id": user_id,
        "username": username,
        "email": email,
        "hashed_password": hashed,
        "created_at": datetime.utcnow()
    }
    return User(**users_db[user_id])

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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
    
    user_data = users_db.get(user_id)
    if user_data is None:
        raise credentials_exception
    
    return User(**user_data)

# ==================== API 路由 ====================

@app.get("/")
async def root():
    return {"message": "LiteKB API", "version": "0.1.0"}

@app.post("/api/v1/auth/register", response_model=User)
async def register(user: UserCreate):
    for u in users_db.values():
        if u["username"] == user.username:
            raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(user.username, user.password, user.email)

@app.post("/api/v1/auth/login", response_model=Token)
async def login(user: UserLogin):
    found = None
    for u in users_db.values():
        if u["username"] == user.username:
            found = u
            break
    
    if not found or not verify_password(user.password, found["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": found["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/v1/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ==================== 知识库 API ====================

@app.post("/api/v1/kb", response_model=KnowledgeBase)
async def create_kb(
    kb: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user)
):
    kb_id = str(uuid.uuid4())
    kb_db[kb_id] = {
        "id": kb_id,
        "name": kb.name,
        "description": kb.description,
        "doc_count": 0,
        "created_by": current_user.id,
        "created_at": datetime.utcnow()
    }
    return KnowledgeBase(**kb_db[kb_id])

@app.get("/api/v1/kb", response_model=List[KnowledgeBase])
async def list_kbs(current_user: User = Depends(get_current_user)):
    return [KnowledgeBase(**v) for v in kb_db.values()]

@app.get("/api/v1/kb/{kb_id}", response_model=KnowledgeBase)
async def get_kb(kb_id: str, current_user: User = Depends(get_current_user)):
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return KnowledgeBase(**kb_db[kb_id])

@app.put("/api/v1/kb/{kb_id}")
async def update_kb(
    kb_id: str,
    data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user)
):
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    kb_db[kb_id].update({
        "name": data.name,
        "description": data.description
    })
    return kb_db[kb_id]

@app.delete("/api/v1/kb/{kb_id}")
async def delete_kb(kb_id: str, current_user: User = Depends(get_current_user)):
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    del kb_db[kb_id]
    return {"message": "deleted"}

# ==================== 文档 API ====================

@app.post("/api/v1/kb/{kb_id}/docs", response_model=Document)
async def create_doc(
    kb_id: str,
    doc: DocumentCreate,
    current_user: User = Depends(get_current_user)
):
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    doc_id = str(uuid.uuid4())
    doc_db[doc_id] = {
        "id": doc_id,
        "kb_id": kb_id,
        "title": doc.title,
        "content": doc.content,
        "status": "indexed",
        "created_at": datetime.utcnow()
    }
    
    kb_db[kb_id]["doc_count"] += 1
    
    return Document(**doc_db[doc_id])

@app.post("/api/v1/kb/{kb_id}/docs/upload")
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传文档文件"""
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # 读取文件内容
    content = await file.read()
    filename = file.filename or "document"
    
    # 处理文档
    from app.services.document import document_service
    doc = await document_service.create_document(
        kb_id=kb_id,
        title=filename,
        content=content,
        filename=filename
    )
    
    return {
        "id": doc.id,
        "title": doc.title,
        "status": doc.status,
        "message": "文档上传成功"
    }

@app.get("/api/v1/kb/{kb_id}/docs", response_model=List[Document])
async def list_documents(
    kb_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    docs = [Document(**d) for d in doc_db.values() if d.get("kb_id") == kb_id]
    return docs[skip:skip+limit]

@app.delete("/api/v1/kb/{kb_id}/docs/{doc_id}")
async def delete_document(
    kb_id: str,
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    if doc_id not in doc_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    del doc_db[doc_id]
    if kb_id in kb_db:
        kb_db[kb_id]["doc_count"] = max(0, kb_db[kb_id]["doc_count"] - 1)
    
    return {"message": "deleted"}

# ==================== 搜索 API ====================

@app.post("/api/v1/kb/{kb_id}/search")
async def search_kb(
    kb_id: str,
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """混合检索"""
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    from app.services.search import hybrid_search
    
    results = await hybrid_search.search(
        query=request.query,
        kb_id=kb_id,
        strategy=request.strategy,
        top_k=request.top_k,
        filters=request.filters
    )
    
    return {
        "results": [
            {
                "id": r.id,
                "title": r.metadata.get("source", "Unknown"),
                "content": r.content[:500],
                "score": r.score,
                "type": r.source_type
            }
            for r in results
        ],
        "strategy": request.strategy
    }

# ==================== RAG 对话 API ====================

@app.post("/api/v1/kb/{kb_id}/chat", response_model=ChatResponse)
async def chat_with_kb(
    kb_id: str,
    chat: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """RAG 对话"""
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    from app.services.rag import rag_engine
    
    history = [{"role": m.role, "content": m.content} for m in (chat.history or [])]
    
    response = await rag_engine.query(
        kb_id=kb_id,
        question=chat.message,
        mode=chat.mode,
        history=history
    )
    
    return ChatResponse(
        answer=response.answer,
        sources=response.sources,
        conversation_id=response.conversation_id
    )

@app.post("/api/v1/kb/{kb_id}/chat/stream")
async def stream_chat(
    kb_id: str,
    chat: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """流式 RAG 对话 (SSE)"""
    # TODO: 实现 SSE 流式响应
    return await chat_with_kb(kb_id, chat, current_user)

# ==================== 知识图谱 API ====================

@app.get("/api/v1/kb/{kb_id}/graph")
async def get_graph(kb_id: str, current_user: User = Depends(get_current_user)):
    """获取知识图谱"""
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    from app.services.graph import graph_service
    
    return graph_service.get_graph(kb_id)

@app.post("/api/v1/kb/{kb_id}/graph/build")
async def build_graph(
    kb_id: str,
    rebuild: bool = False,
    current_user: User = Depends(get_current_user)
):
    """构建/重建知识图谱"""
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    from app.services.graph import graph_service
    
    # 获取知识库所有文档
    docs = [d for d in doc_db.values() if d.get("kb_id") == kb_id and d.get("content")]
    
    stats = {"entities": 0, "relations": 0}
    for doc in docs:
        result = await graph_service.build_graph(
            kb_id=kb_id,
            doc_id=doc["id"],
            text=doc["content"][:5000]  # 限制长度
        )
        stats["entities"] += result["entities"]
        stats["relations"] += result["relations"]
    
    return {
        "message": "图谱构建完成",
        **stats
    }

@app.get("/api/v1/kb/{kb_id}/graph/search")
async def search_graph(
    kb_id: str,
    q: str,
    current_user: User = Depends(get_current_user)
):
    """搜索图谱实体"""
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    from app.services.graph import graph_service
    
    return graph_service.search_entities(kb_id, q)

@app.get("/api/v1/kb/{kb_id}/graph/entity/{entity_id}")
async def get_entity(
    kb_id: str,
    entity_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取实体详情"""
    from app.services.graph import graph_service
    
    return graph_service.get_entity_relations(kb_id, entity_id)

# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
