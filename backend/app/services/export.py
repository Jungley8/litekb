"""
导出服务 - 支持多种格式导出
"""
from typing import List, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod
import json
import markdown


class ExportFormatter(ABC):
    """导出格式基类"""
    
    @abstractmethod
    def format(self, data: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    def get_extension(self) -> str:
        pass
    
    @abstractmethod
    def get_content_type(self) -> str:
        pass


class MarkdownFormatter(ExportFormatter):
    """Markdown 格式"""
    
    def format(self, data: Dict[str, Any]) -> str:
        lines = [
            f"# {data.get('title', 'Knowledge Base Export')}",
            f"\n*导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            "\n---\n",
        ]
        
        # 知识库信息
        if 'kb_info' in data:
            kb = data['kb_info']
            lines.append(f"## {kb.get('name', '')}")
            if kb.get('description'):
                lines.append(f"\n{kb['description']}\n")
        
        # 文档列表
        if 'documents' in data:
            lines.append("\n## 文档列表\n")
            for i, doc in enumerate(data['documents'], 1):
                lines.append(f"### {i}. {doc.get('title', 'Untitled')}")
                if doc.get('content'):
                    lines.append(f"\n{doc['content'][:500]}...")
                lines.append("\n")
        
        # 对话历史
        if 'conversations' in data:
            lines.append("\n## 对话历史\n")
            for conv in data['conversations']:
                lines.append(f"### Q: {conv.get('question', '')}")
                lines.append(f"\nA: {conv.get('answer', '')}\n")
                lines.append(f"\n*来源: {', '.join(conv.get('sources', []))}*\n")
        
        return '\n'.join(lines)
    
    def get_extension(self) -> str:
        return '.md'
    
    def get_content_type(self) -> str:
        return 'text/markdown'


class JSONFormatter(ExportFormatter):
    """JSON 格式"""
    
    def format(self, data: Dict[str, Any]) -> str:
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "version": "1.0",
            **data
        }
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    def get_extension(self) -> str:
        return '.json'
    
    def get_content_type(self) -> str:
        return 'application/json'


class HTMLFormatter(ExportFormatter):
    """HTML 格式"""
    
    def format(self, data: Dict[str, Any]) -> str:
        md_content = MarkdownFormatter().format(data)
        html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
        
        template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{data.get('title', 'Export')}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #18a058; }}
        h2 {{ color: #2080f0; margin-top: 30px; }}
        h3 {{ color: #d03050; }}
        pre {{ background: #f5f5f5; padding: 15px; border-radius: 8px; overflow-x: auto; }}
        code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }}
        .metadata {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
{html}
</body>
</html>
        """
        return template.strip()
    
    def get_extension(self) -> str:
        return '.html'
    
    def get_content_type(self) -> str:
        return 'text/html'


class CSVFormatter(ExportFormatter):
    """CSV 格式 (用于文档列表)"""
    
    def format(self, data: Dict[str, Any]) -> str:
        if 'documents' not in data:
            return ""
        
        lines = ['标题,类型,创建时间,状态,预览']
        
        for doc in data['documents']:
            preview = (doc.get('content', '') or '')[:100].replace(',', '，').replace('\n', ' ')
            lines.append(f"{doc.get('title', '')},{doc.get('file_type', '')},{doc.get('created_at', '')},{doc.get('status', '')},{preview}")
        
        return '\n'.join(lines)
    
    def get_extension(self) -> str:
        return '.csv'
    
    def get_content_type(self) -> str:
        return 'text/csv'


class ExportService:
    """导出服务"""
    
    FORMATTERS = {
        'markdown': MarkdownFormatter,
        'json': JSONFormatter,
        'html': HTMLFormatter,
        'csv': CSVFormatter,
    }
    
    def __init__(self):
        self.formatters = {k: v() for k, v in self.FORMATTERS.items()}
    
    def export_knowledge_base(
        self,
        kb_id: str,
        kb_info: Dict,
        documents: List[Dict],
        format: str = 'markdown',
        include_conversations: bool = False
    ) -> Dict[str, Any]:
        """导出知识库"""
        data = {
            'title': f"{kb_info.get('name', 'Export')} - {datetime.now().strftime('%Y%m%d')}",
            'kb_info': kb_info,
            'documents': [
                {
                    'title': doc.get('title'),
                    'file_type': doc.get('file_type'),
                    'content': doc.get('content'),
                    'created_at': doc.get('created_at'),
                    'status': doc.get('status'),
                }
                for doc in documents
            ]
        }
        
        if include_conversations:
            # TODO: 获取对话历史
            pass
        
        formatter = self.formatters.get(format)
        if not formatter:
            raise ValueError(f"Unsupported format: {format}")
        
        return {
            'content': formatter.format(data),
            'filename': f"{kb_info.get('slug', 'export')}_{datetime.now().strftime('%Y%m%d')}{formatter.get_extension()}",
            'content_type': formatter.get_content_type()
        }
    
    def export_document(self, doc: Dict, format: str = 'markdown') -> Dict[str, Any]:
        """导出单个文档"""
        data = {
            'title': doc.get('title', 'Document'),
            'documents': [{
                'title': doc.get('title'),
                'content': doc.get('content'),
                'file_type': doc.get('file_type'),
                'created_at': doc.get('created_at'),
            }]
        }
        
        formatter = self.formatters.get(format)
        return {
            'content': formatter.format(data),
            'filename': f"{doc.get('title', 'document')}{formatter.get_extension()}",
            'content_type': formatter.get_content_type()
        }
    
    def get_supported_formats(self) -> List[Dict[str, str]]:
        """获取支持的格式"""
        return [
            {'id': k, 'name': v.__class__.__name__.replace('Formatter', '').title()}
            for k, v in self.formatters.items()
        ]


# 全局实例
export_service = ExportService()
