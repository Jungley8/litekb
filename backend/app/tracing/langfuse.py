"""
Langfuse 可观测性集成
"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger
from functools import wraps
from contextlib import contextmanager


class LangfuseClient:
    """Langfuse 客户端 - 可回退"""
    
    def __init__(self):
        self._client = None
        self._enabled = False
        self._init_client()
    
    def _init_client(self):
        """初始化 Langfuse 客户端"""
        # 检查是否启用
        self._enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
        
        if not self._enabled:
            logger.info("Langfuse disabled, using local tracing only")
            return
        
        # 尝试导入 langfuse
        try:
            from langfuse import Langfuse
            from langfuse.decorators import langfuse_context
            
            self._client = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
            
            logger.info("Langfuse initialized successfully")
            
        except ImportError:
            logger.warning("langfuse not installed, using local tracing")
            self._enabled = False
        
        except Exception as e:
            logger.warning(f"Langfuse init failed: {e}, using local tracing")
            self._enabled = False
    
    @property
    def client(self):
        """获取客户端"""
        return self._client
    
    @property
    def enabled(self) -> bool:
        """是否启用"""
        return self._enabled and self._client is not None
    
    # ========== Trace 管理 ==========
    
    def create_trace(
        self,
        name: str,
        metadata: Dict = None,
        user_id: str = None,
    ) -> "Trace":
        """创建追踪"""
        if not self.enabled:
            return LocalTrace(name, metadata)
        
        try:
            trace = self._client.trace(
                name=name,
                metadata=metadata,
                user_id=user_id,
            )
            return LangfuseTrace(trace)
        except Exception as e:
            logger.error(f"Create trace failed: {e}")
            return LocalTrace(name, metadata)
    
    @contextmanager
    def trace_context(
        self,
        name: str,
        metadata: Dict = None,
        user_id: str = None,
    ):
        """追踪上下文"""
        if not self.enabled:
            yield LocalTrace(name, metadata)
            return
        
        try:
            with self._client.trace(
                name=name,
                metadata=metadata,
                user_id=user_id,
            ) as trace:
                yield LangfuseTrace(trace)
        except Exception as e:
            logger.error(f"Trace context failed: {e}")
            yield LocalTrace(name, metadata)
    
    # ========== Generation 管理 ==========
    
    def create_generation(
        self,
        trace,
        name: str,
        prompt: str,
        model: str,
        completion: str = None,
        metadata: Dict = None,
        input_cost: float = None,
        output_cost: float = None,
        **kwargs
    ) -> "Generation":
        """创建生成记录"""
        if not self.enabled:
            return LocalGeneration(name, prompt, model, completion)
        
        try:
            generation = trace.generation(
                name=name,
                input=prompt,
                model=model,
                output=completion,
                metadata=metadata,
            )
            return LangfuseGeneration(generation)
        except Exception as e:
            logger.error(f"Create generation failed: {e}")
            return LocalGeneration(name, prompt, model, completion)
    
    # ========== Span 管理 ==========
    
    def create_span(
        self,
        trace,
        name: str,
        metadata: Dict = None,
        **kwargs
    ) -> "Span":
        """创建跨度"""
        if not self.enabled:
            return LocalSpan(name, metadata)
        
        try:
            span = trace.span(
                name=name,
                metadata=metadata,
            )
            return LangfuseSpan(span)
        except Exception as e:
            logger.error(f"Create span failed: {e}")
            return LocalSpan(name, metadata)
    
    # ========== Event 管理 ==========
    
    def create_event(
        self,
        trace,
        name: str,
        metadata: Dict = None,
    ):
        """创建事件"""
        if not self.enabled:
            return
        
        try:
            trace.event(name=name, metadata=metadata)
        except Exception as e:
            logger.error(f"Create event failed: {e}")
    
    # ========== 提示词管理 ==========
    
    def get_prompt(
        self,
        name: str,
        version: int = None,
    ) -> Optional[Dict]:
        """获取提示词"""
        if not self.enabled:
            return None
        
        try:
            prompt = self._client.get_prompt(
                name=name,
                version=version,
            )
            return {
                "name": prompt.name,
                "prompt": prompt.prompt,
                "version": prompt.version,
                "config": prompt.config,
            }
        except Exception as e:
            logger.warning(f"Get prompt failed: {e}")
            return None
    
    def create_prompt(
        self,
        name: str,
        prompt: str,
        version: int = None,
        config: Dict = None,
    ) -> Optional[Dict]:
        """创建/更新提示词"""
        if not self.enabled:
            return None
        
        try:
            prompt = self._client.create_prompt(
                name=name,
                prompt=prompt,
                version=version,
                config=config or {},
            )
            return {
                "name": prompt.name,
                "prompt": prompt.prompt,
                "version": prompt.version,
            }
        except Exception as e:
            logger.warning(f"Create prompt failed: {e}")
            return None
    
    def update_prompt(
        self,
        name: str,
        prompt: str,
        version: int = None,
    ) -> Optional[Dict]:
        """更新提示词版本"""
        if not self.enabled:
            return None
        
        try:
            # 获取当前版本
            current = self.get_prompt(name)
            new_version = version or (current["version"] + 1 if current else 1)
            
            return self.create_prompt(name, prompt, new_version)
        except Exception as e:
            logger.warning(f"Update prompt failed: {e}")
            return None


# ========== 本地追踪类 (回退) ==========

class LocalTrace:
    """本地追踪 - 回退实现"""
    
    def __init__(self, name: str, metadata: Dict = None):
        self.name = name
        self.metadata = metadata or {}
        self.generations: List = []
        self.spans: List = []
        self.events: List = []
        self.start_time = datetime.utcnow()
    
    def generation(self, **kwargs):
        """创建生成"""
        gen = LocalGeneration(
            name=kwargs.get("name", "generation"),
            prompt=kwargs.get("input", ""),
            model=kwargs.get("model", ""),
            completion=kwargs.get("output"),
        )
        self.generations.append(gen)
        return gen
    
    def span(self, **kwargs):
        """创建跨度"""
        span = LocalSpan(
            name=kwargs.get("name", "span"),
            metadata=kwargs.get("metadata", {}),
        )
        self.spans.append(span)
        return span
    
    def event(self, name: str, metadata: Dict = None):
        """记录事件"""
        self.events.append({
            "name": name,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow(),
        })
    
    def end(self, metadata: Dict = None):
        """结束追踪"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()


class LangfuseTrace:
    """Langfuse 追踪包装"""
    
    def __init__(self, trace):
        self._trace = trace
    
    def generation(self, **kwargs):
        return LangfuseGeneration(
            self._trace.generation(**kwargs)
        )
    
    def span(self, **kwargs):
        return LangfuseSpan(
            self._trace.span(**kwargs)
        )
    
    def event(self, name: str, metadata: Dict = None):
        self._trace.event(name=name, metadata=metadata)
    
    def end(self, metadata: Dict = None):
        self._trace.end(metadata=metadata)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()


class LocalGeneration:
    """本地生成 - 回退实现"""
    
    def __init__(self, name: str, prompt: str, model: str, completion: str = None):
        self.name = name
        self.prompt = prompt
        self.model = model
        self.completion = completion
        self.metadata: Dict = {}
        self.start_time = datetime.utcnow()
        self.end_time = None
        self.input_tokens = 0
        self.output_tokens = 0
    
    def end(
        self,
        completion: str = None,
        usage: Dict = None,
        metadata: Dict = None,
    ):
        """结束生成"""
        self.completion = completion or self.completion
        self.end_time = datetime.utcnow()
        self.metadata = metadata or {}
        
        if usage:
            self.input_tokens = usage.get("input_tokens", 0)
            self.output_tokens = usage.get("output_tokens", 0)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()


class LangfuseGeneration:
    """Langfuse 生成包装"""
    
    def __init__(self, generation):
        self._gen = generation
    
    def end(
        self,
        completion: str = None,
        usage: Dict = None,
        metadata: Dict = None,
    ):
        self._gen.end(
            output=completion,
            usage=usage,
            metadata=metadata,
        )


class LocalSpan:
    """本地跨度 - 回退实现"""
    
    def __init__(self, name: str, metadata: Dict = None):
        self.name = name
        self.metadata = metadata or {}
        self.events: List = []
        self.start_time = datetime.utcnow()
        self.end_time = None
    
    def event(self, name: str, metadata: Dict = None):
        self.events.append({
            "name": name,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow(),
        })
    
    def end(self, metadata: Dict = None):
        self.end_time = datetime.utcnow()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()


class LangfuseSpan:
    """Langfuse 跨度包装"""
    
    def __init__(self, span):
        self._span = span
    
    def event(self, name: str, metadata: Dict = None):
        self._span.event(name=name, metadata=metadata)
    
    def end(self, metadata: Dict = None):
        self._span.end(metadata=metadata)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()


# 全局实例
langfuse = LangfuseClient()
