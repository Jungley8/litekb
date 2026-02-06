"""
提示词管理器 - Langfuse 集成
"""
import os
from typing import Dict, Any, Optional, List
from loguru import logger


# 默认提示词模板
DEFAULT_PROMPTS = {
    # RAG
    "rag_naive": {
        "prompt": """你是知识库助手。请基于以下上下文回答用户的问题。

上下文：
{context}

用户问题：{question}

要求：
1. 只基于上下文回答，标注引用来源
2. 回答简洁明了
3. 不确定时说明""",
        "description": "RAG 基础提示词",
    },
    
    "rag_contextual": {
        "prompt": """你是知识库助手。基于上下文和对话历史回答问题。

对话历史：
{history}

上下文：
{context}

当前问题：{question}

要求：
1. 结合历史和上下文回答
2. 标注引用来源
3. 保持对话连贯""",
        "description": "带上下文的 RAG",
    },
    
    "rag_graph": {
        "prompt": """你是知识库助手。结合知识图谱和文档内容回答问题。

知识图谱：
{graph_context}

相关文档：
{doc_context}

问题：{question}

要求：
1. 综合图谱和文档信息
2. 标注信息来源""",
        "description": "图谱增强 RAG",
    },
    
    # 文件解析
    "doc_summarize": {
        "prompt": """请为以下文档生成摘要：

{content}

要求：
1. 摘要不超过 {max_length} 字
2. 提取 3-5 个关键要点
3. 保持原意

摘要：""",
        "description": "文档摘要",
    },
    
    "doc_chunk": {
        "prompt": """请将以下文档分割成语义完整的 chunks：

{content}

要求：
1. 每个 chunk 300-500 字
2. 保持语义完整
3. 保留关键信息

Chunks：""",
        "description": "文档分块",
    },
    
    # 图谱
    "entity_extraction": {
        "prompt": """从以下文本中提取实体和关系：

文本：
{text}

格式：
实体：entity_name | entity_type
关系：(entity1) --relation--> (entity2)

实体：""",
        "description": "实体抽取",
    },
    
    "relation_extraction": {
        "prompt": """分析以下文本中的实体关系：

{text}

已知实体：
{entities}

请为每对相关实体标注关系类型。""",
        "description": "关系抽取",
    },
    
    "graph_query": {
        "prompt": """基于知识图谱回答问题。

图谱查询结果：
{graph_result}

相关文档：
{doc_result}

请综合以上信息回答：{question}""",
        "description": "图谱查询",
    },
}


class PromptManager:
    """提示词管理器 - 集成 Langfuse"""
    
    def __init__(self):
        self._langfuse_client = None
        self._enabled = False
        self._init_langfuse()
    
    def _init_langfuse(self):
        """初始化 Langfuse"""
        self._enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
        
        if not self._enabled:
            logger.info("PromptManager: Langfuse disabled, using defaults")
            return
        
        try:
            from langfuse import Langfuse
            self._langfuse_client = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
            logger.info("PromptManager: Langfuse initialized")
        except Exception as e:
            logger.warning(f"PromptManager: Langfuse init failed: {e}")
            self._enabled = False
    
    def get_prompt(self, name: str, variables: Dict[str, str] = None) -> str:
        """
        获取并渲染提示词
        
        Args:
            name: 提示词名称 (如 rag_naive, entity_extraction)
            variables: 变量替换
            
        Returns:
            渲染后的提示词
        """
        prompt_text = None
        
        # 1. 优先从 Langfuse 获取
        if self._enabled and self._langfuse_client:
            try:
                langfuse_prompt = self._langfuse_client.get_prompt(name=name)
                if langfuse_prompt:
                    prompt_text = langfuse_prompt.prompt
                    logger.debug(f"Prompt from Langfuse: {name}")
            except Exception as e:
                logger.debug(f"Langfuse prompt not found: {name}")
        
        # 2. 回退到默认模板
        if not prompt_text:
            if name in DEFAULT_PROMPTS:
                prompt_text = DEFAULT_PROMPTS[name]["prompt"]
                logger.debug(f"Prompt from defaults: {name}")
            else:
                logger.warning(f"Prompt not found: {name}")
                return ""
        
        # 3. 渲染变量
        if variables:
            for key, value in variables.items():
                prompt_text = prompt_text.replace(f"{{{{{key}}}}}", str(value))
                prompt_text = prompt_text.replace(f"${{{key}}}", str(value))
        
        return prompt_text
    
    def get_raw_prompt(self, name: str) -> Optional[str]:
        """获取原始提示词"""
        if self._enabled and self._langfuse_client:
            try:
                prompt = self._langfuse_client.get_prompt(name=name)
                return prompt.prompt
            except:
                pass
        
        if name in DEFAULT_PROMPTS:
            return DEFAULT_PROMPTS[name]["prompt"]
        
        return None
    
    def sync_to_langfuse(self, name: str) -> bool:
        """同步默认提示词到 Langfuse"""
        if not self._enabled:
            return False
        
        if name not in DEFAULT_PROMPTS:
            return False
        
        try:
            prompt_data = DEFAULT_PROMPTS[name]
            self._langfuse_client.create_prompt(
                name=name,
                prompt=prompt_data["prompt"],
                config={"description": prompt_data["description"]}
            )
            logger.info(f"Synced prompt to Langfuse: {name}")
            return True
        except Exception as e:
            logger.error(f"Sync prompt failed: {e}")
            return False
    
    def sync_all_to_langfuse(self):
        """同步所有默认提示词到 Langfuse"""
        if not self._enabled:
            logger.warning("Langfuse not enabled")
            return
        
        for name in DEFAULT_PROMPTS:
            self.sync_to_langfuse(name)
        
        logger.info("All prompts synced to Langfuse")
    
    def list_available_prompts(self) -> List[Dict]:
        """列出可用提示词"""
        prompts = []
        
        # Langfuse 提示词
        if self._enabled and self._langfuse_client:
            try:
                from langfuse import Langfuse
                all_prompts = self._langfuse_client.get_prompts()
                for p in all_prompts.data:
                    prompts.append({
                        "name": p.name,
                        "version": p.version,
                        "source": "langfuse",
                    })
            except Exception as e:
                logger.debug(f"List Langfuse prompts failed: {e}")
        
        # 默认提示词
        for name, config in DEFAULT_PROMPTS.items():
            if not any(p["name"] == name for p in prompts):
                prompts.append({
                    "name": name,
                    "version": 1,
                    "source": "default",
                    "description": config["description"],
                })
        
        return prompts


# 全局实例
prompt_manager = PromptManager()


# ============== 便捷函数 =============

def get_prompt(name: str, variables: Dict[str, str] = None) -> str:
    """获取提示词"""
    return prompt_manager.get_prompt(name, variables)


def render_prompt(name: str, **variables) -> str:
    """渲染提示词"""
    return prompt_manager.get_prompt(name, variables)


def rag_prompt(
    mode: str = "naive",
    question: str = "",
    context: str = "",
    history: str = "",
    graph_context: str = "",
) -> str:
    """获取 RAG 提示词"""
    prompt_name = f"rag_{mode}"
    
    variables = {
        "question": question,
        "context": context,
        "history": history or "无",
        "graph_context": graph_context or "无",
    }
    
    return get_prompt(prompt_name, variables)


def entity_extraction_prompt(text: str) -> str:
    """实体抽取提示词"""
    return get_prompt("entity_extraction", {"text": text})


def summarize_prompt(content: str, max_length: str = "200") -> str:
    """摘要提示词"""
    return get_prompt("doc_summarize", {
        "content": content,
        "max_length": max_length,
    })


def graph_query_prompt(question: str, graph_result: str, doc_result: str) -> str:
    """图谱查询提示词"""
    return get_prompt("graph_query", {
        "question": question,
        "graph_result": graph_result,
        "doc_result": doc_result,
    })
