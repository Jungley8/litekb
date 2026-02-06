"""
导出服务
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger


class ExportService:
    """导出服务"""
    
    SUPPORTED_FORMATS = ["markdown", "json", "html", "csv"]
    
    async def export_kb(
        self,
        kb_id: str,
        format: str = "markdown",
        include_metadata: bool = True,
    ) -> Dict:
        """导出知识库"""
        
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的格式: {format}")
        
        # 获取知识库内容
        documents = await self._get_documents(kb_id)
        
        # 按格式导出
        if format == "markdown":
            content = self._export_markdown(documents, include_metadata)
            filename = f"kb_{kb_id}_{datetime.now().strftime('%Y%m%d')}.md"
        elif format == "json":
            content = self._export_json(documents, include_metadata)
            filename = f"kb_{kb_id}_{datetime.now().strftime('%Y%m%d')}.json"
        elif format == "html":
            content = self._export_html(documents, include_metadata)
            filename = f"kb_{kb_id}_{datetime.now().strftime('%Y%m%d')}.html"
        elif format == "csv":
            content = self._export_csv(documents)
            filename = f"kb_{kb_id}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return {
            "filename": filename,
            "content": content,
            "format": format,
            "doc_count": len(documents),
        }
    
    async def export_chat(
        self,
        chat_id: str,
        format: str = "markdown",
    ) -> Dict:
        """导出对话"""
        
        # TODO: 获取对话历史
        messages = [
            {"role": "user", "content": "示例问题"},
            {"role": "assistant", "content": "这是回答。"},
        ]
        
        if format == "markdown":
            content = self._export_chat_markdown(messages)
        elif format == "json":
            import json
            content = json.dumps({"messages": messages}, ensure_ascii=False, indent=2)
        else:
            content = str(messages)
        
        return {
            "filename": f"chat_{chat_id}_{datetime.now().strftime('%Y%m%d')}.{format}",
            "content": content,
            "format": format,
        }
    
    async def _get_documents(self, kb_id: str) -> List[Dict]:
        """获取文档列表"""
        # TODO: 从数据库查询
        return [
            {
                "id": "1",
                "title": "文档 1",
                "content": "这是文档内容...",
                "created_at": datetime.now().isoformat(),
            }
        ]
    
    def _export_markdown(
        self,
        documents: List[Dict],
        include_metadata: bool = True,
    ) -> str:
        """导出为 Markdown"""
        
        lines = ["# 知识库导出\n"]
        
        for doc in documents:
            lines.append(f"## {doc['title']}\n")
            
            if include_metadata:
                lines.append(f"*创建时间: {doc.get('created_at', 'N/A')}*\n")
            
            lines.append(f"\n{doc.get('content', '')}\n")
            lines.append("\n---\n")
        
        return "\n".join(lines)
    
    def _export_json(
        self,
        documents: List[Dict],
        include_metadata: bool = True,
    ) -> str:
        """导出为 JSON"""
        
        import json
        
        data = {
            "exported_at": datetime.now().isoformat(),
            "document_count": len(documents),
            "documents": documents,
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _export_html(
        self,
        documents: List[Dict],
        include_metadata: bool = True,
    ) -> str:
        """导出为 HTML"""
        
        html = [
            "<!DOCTYPE html>",
            "<html><head>",
            "<meta charset='utf-8'>",
            "<title>知识库导出</title>",
            "<style>",
            "body { font-family: Arial; max-width: 800px; margin: 0 auto; padding: 20px; }",
            "h1, h2 { color: #333; }",
            "hr { border: none; border-top: 1px solid #eee; margin: 20px 0; }",
            ".metadata { color: #666; font-size: 14px; }",
            "</style>",
            "</head><body>",
            "<h1>📚 知识库导出</h1>",
            f"<p>导出时间: {datetime.now().isoformat()}</p>",
            f"<p>文档数量: {len(documents)}</p>",
        ]
        
        for doc in documents:
            html.append("<hr>")
            html.append(f"<h2>{doc['title']}</h2>")
            
            if include_metadata:
                html.append(f"<p class='metadata'>创建时间: {doc.get('created_at', 'N/A')}</p>")
            
            html.append(f"<pre>{doc.get('content', '')}</pre>")
        
        html.append("</body></html>")
        
        return "\n".join(html)
    
    def _export_csv(self, documents: List[Dict]) -> str:
        """导出为 CSV"""
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["ID", "标题", "内容", "创建时间"])
        
        for doc in documents:
            writer.writerow([
                doc.get("id", ""),
                doc.get("title", ""),
                doc.get("content", ""),
                doc.get("created_at", ""),
            ])
        
        return output.getvalue()
    
    def _export_chat_markdown(self, messages: List[Dict]) -> str:
        """导出对话为 Markdown"""
        
        lines = ["# 对话导出\n", f"导出时间: {datetime.now().isoformat()}\n"]
        
        for msg in messages:
            role = "👤 用户" if msg.get("role") == "user" else "🤖 助手"
            lines.append(f"## {role}\n")
            lines.append(f"{msg.get('content', '')}\n")
            lines.append("\n---\n")
        
        return "\n".join(lines)


# 全局实例
export_service = ExportService()
