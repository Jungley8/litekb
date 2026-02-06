"""
RAG 摘要生成服务
"""
from typing import Optional, List, Dict
from loguru import logger
from dataclasses import dataclass


@dataclass
class DocumentSummary:
    """文档摘要"""
    doc_id: str
    title: str
    summary: str
    key_points: List[str]
    entities: List[str]
    categories: List[str]


class SummaryGenerator:
    """摘要生成器"""
    
    def __init__(self, llm_client = None):
        self.llm = llm_client
    
    async def generate_summary(
        self,
        doc_id: str,
        title: str,
        content: str,
        max_length: int = 500,
    ) -> DocumentSummary:
        """为文档生成摘要"""
        
        prompt = f"""请为以下文档生成摘要：

标题: {title}

内容:
{content[:3000]}

请用中文生成:
1. 简短摘要 (不超过 {max_length} 字)
2. 关键要点 (3-5 条)
3. 核心实体 (5-10 个)
4. 分类标签 (2-3 个)

JSON 格式返回:
{{
  "summary": "...",
  "key_points": ["...", "..."],
  "entities": ["...", "..."],
  "categories": ["..."]
}}"""
        
        try:
            if self.llm:
                response = await self.llm.agenerate(prompt)
                return self._parse_response(doc_id, title, response)
            else:
                # 使用模拟数据
                return self._mock_summary(doc_id, title)
                
        except Exception as e:
            logger.error(f"Generate summary failed: {e}")
            return self._mock_summary(doc_id, title)
    
    def _parse_response(
        self,
        doc_id: str,
        title: str,
        response: str,
    ) -> DocumentSummary:
        """解析 LLM 响应"""
        import json
        
        try:
            data = json.loads(response)
            return DocumentSummary(
                doc_id=doc_id,
                title=title,
                summary=data.get("summary", ""),
                key_points=data.get("key_points", []),
                entities=data.get("entities", []),
                categories=data.get("categories", []),
            )
        except json.JSONDecodeError:
            return self._mock_summary(doc_id, title)
    
    def _mock_summary(
        self,
        doc_id: str,
        title: str,
    ) -> DocumentSummary:
        """模拟摘要 (用于测试)"""
        return DocumentSummary(
            doc_id=doc_id,
            title=title,
            summary=f"这是关于 {title} 的文档摘要。",
            key_points=[f"{title} 的核心概念", "相关技术与方法", "实践应用场景"],
            entities=[title, "技术文档", "相关主题"],
            categories=["技术", "文档"],
        )
    
    async def generate_batch_summaries(
        self,
        documents: List[Dict],
    ) -> List[DocumentSummary]:
        """批量生成摘要"""
        summaries = []
        
        for doc in documents:
            summary = await self.generate_summary(
                doc_id=doc["id"],
                title=doc["title"],
                content=doc.get("content", ""),
            )
            summaries.append(summary)
        
        return summaries


# 全局实例
summary_generator = SummaryGenerator()


async def enhance_with_summary(
    doc_id: str,
    title: str,
    content: str,
) -> DocumentSummary:
    """增强文档 (生成摘要)"""
    return await summary_generator.generate_summary(doc_id, title, content)
