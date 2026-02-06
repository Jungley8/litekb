"""
提示词版本管理
"""
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from loguru import logger


class PromptManager:
    """提示词版本管理器"""
    
    def __init__(self, prompts_dir: str = "./data/prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict = {}
    
    def save_prompt(
        self,
        name: str,
        prompt: str,
        version: int = None,
        metadata: Dict = None,
    ) -> Dict:
        """
        保存提示词版本
        
        Returns:
            {
                "name": str,
                "version": int,
                "prompt": str,
                "metadata": dict,
                "created_at": str,
            }
        """
        # 获取当前版本
        current = self.get_latest(name)
        new_version = version or (current["version"] + 1 if current else 1)
        
        prompt_data = {
            "name": name,
            "version": new_version,
            "prompt": prompt,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "created_by": metadata.get("created_by", "system"),
        }
        
        # 保存文件
        file_path = self.prompts_dir / f"{name}_v{new_version}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=2)
        
        # 更新缓存
        self._cache[name] = prompt_data
        
        logger.info(f"Prompt saved: {name} v{new_version}")
        
        return prompt_data
    
    def get_prompt(
        self,
        name: str,
        version: int = None,
    ) -> Optional[Dict]:
        """获取提示词"""
        # 先尝试缓存
        if name in self._cache:
            cached = self._cache[name]
            if version is None or cached["version"] == version:
                return cached
        
        # 加载文件
        if version:
            file_path = self.prompts_dir / f"{name}_v{version}.json"
        else:
            # 获取最新版本
            files = list(self.prompts_dir.glob(f"{name}_v*.json"))
            if not files:
                return None
            latest = max(files, key=lambda f: int(f.stem.split('_v')[1]))
            file_path = latest
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._cache[name] = data
            return data
        
        except Exception as e:
            logger.warning(f"Load prompt failed: {e}")
            return None
    
    def get_latest(self, name: str) -> Optional[Dict]:
        """获取最新版本"""
        return self.get_prompt(name)
    
    def list_versions(self, name: str) -> List[Dict]:
        """列出所有版本"""
        files = list(self.prompts_dir.glob(f"{name}_v*.json"))
        versions = []
        
        for file_path in files:
            try:
                version = int(file_path.stem.split('_v')[1])
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                versions.append({
                    "version": version,
                    "created_at": data["created_at"],
                    "created_by": data.get("created_by", "unknown"),
                })
            except Exception as e:
                logger.warning(f"List versions failed: {e}")
        
        # 按版本排序
        versions.sort(key=lambda v: v["version"], reverse=True)
        return versions
    
    def delete_version(self, name: str, version: int) -> bool:
        """删除版本"""
        file_path = self.prompts_dir / f"{name}_v{version}.json"
        
        if file_path.exists():
            file_path.unlink()
            # 清除缓存
            self._cache.pop(name, None)
            logger.info(f"Prompt version deleted: {name} v{version}")
            return True
        
        return False
    
    def compare_versions(
        self,
        name: str,
        version1: int,
        version2: int,
    ) -> Optional[Dict]:
        """比较版本"""
        v1 = self.get_prompt(name, version1)
        v2 = self.get_prompt(name, version2)
        
        if not v1 or not v2:
            return None
        
        return {
            "name": name,
            "version1": {
                "version": v1["version"],
                "prompt": v1["prompt"],
                "created_at": v1["created_at"],
            },
            "version2": {
                "version": v2["version"],
                "prompt": v2["prompt"],
                "created_at": v2["created_at"],
            },
            "diff": {
                "prompt_changed": v1["prompt"] != v2["prompt"],
                "prompt_length_diff": len(v2["prompt"]) - len(v1["prompt"]),
            },
        }
    
    def render_prompt(
        self,
        name: str,
        variables: Dict[str, str] = None,
        version: int = None,
    ) -> str:
        """渲染提示词"""
        prompt = self.get_prompt(name, version)
        
        if not prompt:
            logger.warning(f"Prompt not found: {name}")
            return ""
        
        rendered = prompt["prompt"]
        
        # 替换变量
        if variables:
            for key, value in variables.items():
                rendered = rendered.replace(f"{{{{{key}}}}", str(value))
                rendered = rendered.replace(f"${{{key}}}", str(value))
        
        return rendered


# 预设提示词模板
DEFAULT_PROMPTS = {
    "rag_system": {
        "prompt": """你是知识库助手。基于以下上下文回答问题。

要求：
1. 只基于上下文回答，标注引用来源
2. 复杂问题分点说明
3. 不确定时明确说明

上下文：
{context}

用户问题：{question}""",
        "description": "RAG 系统提示词",
    },
    
    "rag_with_history": {
        "prompt": """你是知识库助手。基于上下文和对话历史回答问题。

对话历史：
{history}

上下文：
{context}

要求：
1. 结合历史和上下文回答
2. 标注引用来源
3. 保持对话连贯

当前问题：{question}""",
        "description": "带历史记录的 RAG 提示词",
    },
    
    "graph_augmented": {
        "prompt": """你是知识库助手。结合知识图谱和文档内容回答问题。

知识图谱信息：
{graph_context}

相关文档：
{doc_context}

要求：
1. 综合图谱和文档信息
2. 标注信息来源
3. 复杂问题使用图谱推理

问题：{question}""",
        "description": "图谱增强 RAG 提示词",
    },
    
    "summarization": {
        "prompt": """请为以下内容生成摘要：

{content}

要求：
1. 摘要不超过 {max_length} 字
2. 提取 3-5 个关键要点
3. 保持原意

摘要：""",
        "description": "文档摘要提示词",
    },
    
    "entity_extraction": {
        "prompt": """从以下文本中提取实体和关系：

文本：
{text}

格式：
实体：entity_name | entity_type
关系：(entity1) --relation--> (entity2)

实体：""",
        "description": "实体抽取提示词",
    },
}


def init_default_prompts(manager: PromptManager):
    """初始化默认提示词"""
    for name, config in DEFAULT_PROMPTS.items():
        existing = manager.get_latest(name)
        if not existing:
            manager.save_prompt(
                name=name,
                prompt=config["prompt"],
                metadata={
                    "description": config["description"],
                    "created_by": "system",
                    "is_default": True,
                }
            )
            logger.info(f"Default prompt initialized: {name}")


# 全局实例
prompt_manager = PromptManager()

# 初始化默认提示词
init_default_prompts(prompt_manager)
