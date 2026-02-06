"""
文档处理服务
"""
import os
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from app.config import settings
from app.models import get_session, Document, DocumentChunk, KBDocument


class DocumentProcessor:
    """文档处理器"""
    
    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """处理文档"""
        # 1. 提取文本
        text = await self.extract_text(file_content, filename)
        
        # 2. 分块
        chunks = self.split_chunks(text)
        
        # 3. 返回结果
        return {
            "title": Path(filename).stem,
            "file_type": self.get_file_type(filename),
            "content": text[:1000],  # 保存前1000字符作为预览
            "chunks": chunks,
            "metadata": metadata or {}
        }
    
    async def extract_text(self, content: bytes, filename: str) -> str:
        """从文件中提取文本"""
        file_type = self.get_file_type(filename)
        
        if file_type in ["txt", "md"]:
            return content.decode("utf-8")
        
        elif file_type == "docx":
            return await self.extract_docx(content)
        
        elif file_type == "pdf":
            return await self.extract_pdf(content)
        
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
    
    def get_file_type(self, filename: str) -> str:
        """获取文件类型"""
        ext = Path(filename).suffix.lower()
        type_map = {
            ".txt": "txt",
            ".md": "md",
            ".markdown": "md",
            ".docx": "docx",
            ".pdf": "pdf"
        }
        return type_map.get(ext, "txt")
    
    async def extract_docx(self, content: bytes) -> str:
        """提取 DOCX 文本"""
        try:
            import docx
            from io import BytesIO
            doc = docx.Document(BytesIO(content))
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            return "\n".join(text_parts)
        except ImportError:
            logger.warning("python-docx 未安装")
            return ""
    
    async def extract_pdf(self, content: bytes) -> str:
        """提取 PDF 文本"""
        # TODO: 实现 PDF 提取
        logger.warning("PDF 提取功能待实现")
        return ""
    
    def split_chunks(self, text: str) -> List[str]:
        """将文本分块"""
        if not text:
            return []
        
        chunks = []
        start = 0
        text = text.replace("\n\n", "\n")
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 如果不是最后一块，尝试在句子边界断开
            if end < len(text):
                # 查找最后一个句号、问号、感叹号或换行
                for sep in [". ", "? ", "! ", "\n"]:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start + self.chunk_size // 2:
                        end = last_sep + len(sep)
                        break
            
            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap
        
        return chunks


class DocumentService:
    """文档服务"""
    
    def __init__(self):
        self.processor = DocumentProcessor()
    
    async def create_document(
        self,
        kb_id: str,
        title: str,
        content: bytes,
        filename: str,
        metadata: Optional[Dict] = None
    ) -> Document:
        """创建文档"""
        session = get_session()
        
        try:
            # 处理文档
            processed = await self.processor.process_document(
                content, filename, metadata
            )
            
            # 保存文档
            doc = Document(
                id=str(uuid.uuid4()),
                title=processed["title"],
                file_type=processed["file_type"],
                content=processed["content"],
                metadata=processed["metadata"],
                status="processing"
            )
            session.add(doc)
            session.flush()
            
            # 创建分块
            chunk_objects = []
            for i, chunk_content in enumerate(processed["chunks"]):
                chunk = DocumentChunk(
                    id=str(uuid.uuid4()),
                    doc_id=doc.id,
                    kb_id=kb_id,
                    chunk_index=i,
                    content=chunk_content,
                    metadata={"source": filename}
                )
                chunk_objects.append(chunk)
                session.add(chunk)
            
            # 关联到知识库
            kb_doc = KBDocument(
                id=str(uuid.uuid4()),
                kb_id=kb_id,
                doc_id=doc.id,
                chunk_count=len(chunk_objects)
            )
            session.add(kb_doc)
            
            session.commit()
            
            # 更新状态
            doc.status = "indexed"
            session.commit()
            
            logger.info(f"文档 {doc.id} 创建成功，包含 {len(chunk_objects)} 个分块")
            
            return doc
            
        except Exception as e:
            session.rollback()
            doc.status = "failed"
            doc.error_message = str(e)
            session.commit()
            raise e
        
        finally:
            session.close()
    
    def get_documents(self, kb_id: str, skip: int = 0, limit: int = 100) -> List[Document]:
        """获取知识库文档列表"""
        session = get_session()
        try:
            docs = session.query(DocumentChunk)\
                .filter(DocumentChunk.kb_id == kb_id)\
                .offset(skip)\
                .limit(limit)\
                .all()
            
            # 去重
            seen = set()
            result = []
            for doc in docs:
                if doc.doc_id not in seen:
                    seen.add(doc.doc_id)
                    # 获取完整文档信息
                    full_doc = session.query(Document).get(doc.doc_id)
                    if full_doc:
                        result.append(full_doc)
            
            return result
        finally:
            session.close()
    
    def get_chunks(self, doc_id: str) -> List[DocumentChunk]:
        """获取文档分块"""
        session = get_session()
        try:
            chunks = session.query(DocumentChunk)\
                .filter(DocumentChunk.doc_id == doc_id)\
                .order_by(DocumentChunk.chunk_index)\
                .all()
            return chunks
        finally:
            session.close()
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        session = get_session()
        try:
            # 删除分块
            session.query(DocumentChunk).filter(DocumentChunk.doc_id == doc_id).delete()
            
            # 删除关联
            session.query(KBDocument).filter(KBDocument.doc_id == doc_id).delete()
            
            # 删除文档
            session.query(Document).filter(Document.id == doc_id).delete()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


# 全局服务实例
document_service = DocumentService()
