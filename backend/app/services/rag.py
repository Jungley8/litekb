"""
RAG 引擎 - Langfuse 提示词
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

from app.config import settings
from app.services.search import hybrid_search, SearchResult
from app.services.prompt import get_prompt
from app.models import get_session, Message, Conversation


@dataclass
class RAGResponse:
    """RAG 响应"""
    answer: str
    sources: List[Dict[str, Any]]
    conversation_id: str


class LLMClient:
    """LLM 客户端"""
    
    def __init__(self):
        self.provider = settings.llm_provider
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """聊天"""
        if self.provider == "openai":
            return await self._openai_chat(messages, system_prompt, temperature)
        elif self.provider == "ollama":
            return await self._ollama_chat(messages, system_prompt, temperature)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    async def _openai_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        temperature: float
    ) -> str:
        """OpenAI 聊天"""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)
        
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=all_messages,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    async def _ollama_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        temperature: float
    ) -> str:
        """Ollama 本地模型"""
        import httpx
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key="ollama",
            base_url=settings.ollama_url + "/v1"
        )
        
        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)
        
        response = await client.chat.completions.create(
            model=settings.ollama_model,
            messages=all_messages,
            temperature=temperature
        )
        
        return response.choices[0].message.content


class RAGEngine:
    """RAG 引擎"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.search_engine = hybrid_search
    
    async def query(
        self,
        kb_id: str,
        question: str,
        mode: str = "naive",
        history: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
        top_k: int = 5
    ) -> RAGResponse:
        """查询"""
        history = history or []
        
        # 1. 检索
        if mode == "naive":
            chunks = await self.search_engine.search(
                question, kb_id, strategy="hybrid", top_k=top_k
            )
            context = self._build_context(chunks)
        
        elif mode == "contextual":
            # 上下文增强 RAG
            chunks = await self.search_engine.search(
                question, kb_id, strategy="hybrid", top_k=top_k * 2
            )
            # 先生成一个上下文摘要
            summary = await self._summarize_chunks(chunks)
            context = self._build_context_with_summary(summary, chunks[:top_k])
        
        elif mode == "graph-augmented":
            # 图增强 RAG
            graph_context = await self._get_graph_context(kb_id, question)
            chunks = await self.search_engine.search(
                question, kb_id, strategy="hybrid", top_k=top_k
            )
            context = self._combine_context(graph_context, chunks)
        
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        # 2. 构建消息
        messages = [{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}]
        
        # 添加历史
        for msg in history[-5:]:  # 只保留最近5轮
            messages.insert(0, {"role": msg["role"], "content": msg["content"]})
        
        # 3. 调用 LLM
        answer = await self.llm.chat(
            messages,
            system_prompt=system_prompt or self._default_system_prompt()
        )
        
        # 4. 提取来源
        sources = [
            {
                "doc_id": chunk.id,
                "title": chunk.metadata.get("source", "Unknown"),
                "chunk": chunk.content[:300],
                "score": chunk.score
            }
            for chunk in chunks
        ]
        
        # 5. 保存对话
        conv_id = await self._save_conversation(kb_id, question, answer, sources)
        
        return RAGResponse(answer=answer, sources=sources, conversation_id=conv_id)
    
    def _build_context(self, chunks: List[SearchResult]) -> str:
        """构建上下文"""
        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(f"[{i+1}] {chunk.content}")
        return "\n\n".join(context_parts)
    
    def _build_context_with_summary(
        self,
        summary: str,
        chunks: List[SearchResult]
    ) -> str:
        """构建带摘要的上下文"""
        return f"Summary:\n{summary}\n\nRelevant Sections:\n" + \
               "\n\n".join(f"[{i+1}] {c.content}" for i, c in enumerate(chunks))
    
    def _combine_context(
        self,
        graph_context: str,
        chunks: List[SearchResult]
    ) -> str:
        """合并图谱上下文"""
        return f"Knowledge Graph Context:\n{graph_context}\n\nDocument Evidence:\n" + \
               "\n\n".join(f"[{i+1}] {c.content}" for i, c in enumerate(chunks))
    
    async def _summarize_chunks(self, chunks: List[SearchResult]) -> str:
        """摘要"""
        # 使用 LLM 生成摘要
        combined = "\n\n".join(c.content for c in chunks[:5])
        return f"以下是与问题相关的文档内容摘要: {combined[:500]}..."
    
    async def _get_graph_context(self, kb_id: str, query: str) -> str:
        """获取图谱上下文"""
        # 从知识图谱检索相关实体
        return ""
    
    def _default_system_prompt(self) -> str:
        """默认系统提示 - 使用 Langfuse 提示词"""
        return get_prompt("rag_default")
    
    async def _save_conversation(
        self,
        kb_id: str,
        question: str,
        answer: str,
        sources: List[Dict]
    ) -> str:
        """保存对话"""
        import uuid
        from datetime import datetime
        
        session = get_session()
        try:
            conv_id = str(uuid.uuid4())
            
            conv = Conversation(
                id=conv_id,
                kb_id=kb_id,
                title=question[:50],
                updated_at=datetime.utcnow()
            )
            session.add(conv)
            
            user_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                role="user",
                content=question
            )
            assistant_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                role="assistant",
                content=answer,
                sources=sources
            )
            session.add(user_msg)
            session.add(assistant_msg)
            
            session.commit()
            return conv_id
        
        finally:
            session.close()


# 全局实例
rag_engine = RAGEngine()
