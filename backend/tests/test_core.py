"""
单元测试 - 文档处理
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDocumentProcessor:
    """文档处理器测试"""
    
    @pytest.fixture
    def processor(self):
        from app.services.document import DocumentProcessor
        return DocumentProcessor()
    
    @pytest.mark.asyncio
    async def test_extract_txt(self, processor):
        """测试 TXT 提取"""
        content = b"Hello World\nThis is a test document."
        text = await processor.extract_text(content, "test.txt")
        assert "Hello World" in text
        assert "test document" in text
    
    @pytest.mark.asyncio
    async def test_get_file_type(self, processor):
        """测试文件类型识别"""
        assert processor.get_file_type("test.txt") == "txt"
        assert processor.get_file_type("test.md") == "md"
        assert processor.get_file_type("test.docx") == "docx"
        assert processor.get_file_type("test.pdf") == "pdf"
    
    def test_split_chunks(self, processor):
        """测试文本分块"""
        text = "A" * 2500  # 超过 chunk_size
        
        chunks = processor.split_chunks(text)
        
        assert len(chunks) > 1
        # 检查重叠
        if len(chunks) >= 2:
            assert chunks[0][-50:] == chunks[1][:50]
    
    @pytest.mark.asyncio
    async def test_process_document(self, processor):
        """测试完整文档处理"""
        content = b"# Title\n\nThis is a test document with some content."
        
        result = await processor.process_document(
            content,
            "test.md",
            {"author": "test"}
        )
        
        assert result["title"] == "test"
        assert result["file_type"] == "md"
        assert "test document" in result["content"]
        assert len(result["chunks"]) > 0


class TestChunkingStrategies:
    """分块策略测试"""
    
    def test_sentence_boundary_chunks(self):
        """句子边界分块测试"""
        from app.services.document import DocumentProcessor
        processor = DocumentProcessor()
        
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."
        
        chunks = processor.split_chunks(text)
        
        # 应该尽量在句子边界断开
        assert len(chunks) == 1  # 文本较短，应该只有一个块
    
    def test_overlap_preserved(self):
        """重叠保留测试"""
        from app.services.document import DocumentProcessor
        processor = DocumentProcessor()
        
        text = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
        
        chunks = processor.split_chunks(text)
        
        # 检查重叠存在
        if len(chunks) > 1:
            overlap = processor.chunk_overlap
            assert chunks[0][-overlap:] == chunks[1][:overlap]


class TestSearchEngine:
    """搜索引勤测试"""
    
    def test_rrf_fusion(self):
        """RRF 融合排序测试"""
        from app.services.search import rrf_fuse, SearchResult
        
        vector_results = [
            {"id": "doc1", "score": 0.9, "payload": {"content": "content1"}},
            {"id": "doc2", "score": 0.8, "payload": {"content": "content2"}},
        ]
        
        keyword_results = [
            SearchResult(
                id="doc2",
                content="content2",
                score=0.95,
                source_type="keyword",
                metadata={}
            ),
            SearchResult(
                id="doc3",
                content="content3",
                score=0.7,
                source_type="keyword",
                metadata={}
            ),
        ]
        
        results = rrf_fuse(vector_results, keyword_results, top_k=3)
        
        assert len(results) == 3
        # doc2 在两个列表中都出现，应该排名靠前
        assert results[0].id == "doc2"


class TestRAGEngine:
    """RAG 引擎测试"""
    
    def test_build_context(self):
        """上下文构建测试"""
        from app.services.rag import RAGEngine
        from app.services.search import SearchResult
        
        engine = RAGEngine.__new__(RAGEngine)
        
        chunks = [
            SearchResult(
                id="1",
                content="First chunk content",
                score=0.9,
                source_type="vector",
                metadata={}
            ),
            SearchResult(
                id="2",
                content="Second chunk content",
                score=0.8,
                source_type="vector",
                metadata={}
            ),
        ]
        
        context = engine._build_context(chunks)
        
        assert "[1]" in context
        assert "[2]" in context
        assert "First chunk content" in context
    
    def test_default_system_prompt(self):
        """默认系统提示测试"""
        from app.services.rag import RAGEngine
        
        engine = RAGEngine.__new__(RAGEngine)
        prompt = engine._default_system_prompt()
        
        assert "知识库助手" in prompt
        assert "上下文" in prompt


class TestKnowledgeGraph:
    """知识图谱测试"""
    
    def test_entity_structure(self):
        """实体结构测试"""
        from app.services.graph import Entity
        
        entity = Entity(
            id="test_id",
            entity_type="PERSON",
            entity_name="John",
            properties={"age": 30},
            doc_id="doc_1"
        )
        
        assert entity.id == "test_id"
        assert entity.entity_type == "PERSON"
        assert entity.entity_name == "John"
    
    def test_relation_structure(self):
        """关系结构测试"""
        from app.services.graph import Relation
        
        relation = Relation(
            source_id="entity1",
            target_id="entity2",
            relation_type="WORKS_AT",
            confidence=0.95
        )
        
        assert relation.source_id == "entity1"
        assert relation.relation_type == "WORKS_AT"
        assert relation.confidence == 0.95


class TestConfig:
    """配置测试"""
    
    def test_settings_load(self):
        """设置加载测试"""
        from app.config import settings, get_settings
        
        # 测试默认值
        assert settings.app_name == "LiteKB"
        assert settings.chunk_size == 1000
        assert settings.chunk_overlap == 200
        
        # 测试缓存
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestAPIModels:
    """API 模型测试"""
    
    def test_kb_create_model(self):
        """知识库创建模型测试"""
        from app.main import KnowledgeBaseCreate
        
        kb = KnowledgeBaseCreate(
            name="Test KB",
            description="A test knowledge base"
        )
        
        assert kb.name == "Test KB"
        assert kb.description == "A test knowledge base"
    
    def test_chat_request_model(self):
        """对话请求模型测试"""
        from app.main import ChatRequest
        
        chat = ChatRequest(
            kb_id="kb_123",
            message="What is AI?",
            mode="naive"
        )
        
        assert chat.kb_id == "kb_123"
        assert chat.message == "What is AI?"
        assert chat.mode == "naive"


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
