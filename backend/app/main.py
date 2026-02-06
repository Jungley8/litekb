from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import uuid
from contextlib import asynccontextmanager

# ==================== 配置 ====================

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    from app.db import init_db
    init_db()
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
    file_path: Optional[str] = None
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

# ==================== 模拟数据库 ====================

# 简单起见，使用内存数据库演示
# 生产环境请使用 SQLite/PostgreSQL

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
    # 检查是否已存在
    for u in users_db.values():
        if u["username"] == user.username:
            raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(user.username, user.password, user.email)

@app.post("/api/v1/auth/login", response_model=Token)
async def login(user: UserLogin):
    # 查找用户
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

# ==================== 文档 API ====================

@app.post("/api/v1/kb/{kb_id}/docs", response_model=Document)
async def add_document(
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
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    # 更新 KB 文档计数
    kb_db[kb_id]["doc_count"] += 1
    
    return Document(**doc_db[doc_id])

@app.get("/api/v1/kb/{kb_id}/docs", response_model=List[Document])
async def list_documents(
    kb_id: str,
    current_user: User = Depends(get_current_user)
):
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    docs = [Document(**d) for d in doc_db.values() if d.get("kb_id") == kb_id]
    return docs

# ==================== 搜索 API ====================

@app.post("/api/v1/kb/{kb_id}/search")
async def search_kb(
    kb_id: str,
    query: str,
    strategy: str = "hybrid",
    top_k: int = 10,
    current_user: User = Depends(get_current_user)
):
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # 模拟搜索结果
    results = [
        {"id": "1", "title": "示例文档 1", "content": f"这是与 '{query}' 相关的搜索结果...", "score": 0.95},
        {"id": "2", "title": "示例文档 2", "content": f"另一个相关结果...", "score": 0.87},
    ]
    return {"results": results, "strategy": strategy}

# ==================== RAG 对话 API ====================

@app.post("/api/v1/kb/{kb_id}/chat")
async def chat_with_kb(
    kb_id: str,
    chat: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    if kb_id not in kb_db:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # 模拟 RAG 回答
    response = {
        "answer": f"基于知识库内容，关于「{chat.message}」的回答是：这是一个示例回答。在实际实现中，会调用 LLM 并检索相关文档。",
        "sources": [
            {"doc_id": "1", "title": "示例文档 1", "chunk": "相关段落内容..."}
        ],
        "conversation_id": str(uuid.uuid4())
    }
    return response

# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
