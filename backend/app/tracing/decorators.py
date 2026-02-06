"""
LLM 追踪 - 使用 Langfuse API
"""
import os
import time
from typing import Callable, Any, Dict, Optional
from functools import wraps
from datetime import datetime
from loguru import logger
from app.tracing.langfuse import langfuse_tracing


class LLMTracker:
    """LLM 追踪器 - 基于 Langfuse"""
    
    def __init__(self):
        self.enabled = langfuse_tracing.enabled
    
    def trace_call(
        self,
        name: str = "llm_call",
        provider: str = None,
        model: str = None,
    ) -> Callable:
        """LLM 调用追踪装饰器"""
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                trace = None
                generation = None
                
                try:
                    # 创建追踪
                    trace = langfuse_tracing.create_trace(
                        name=f"{name}.{func.__name__}",
                        metadata={
                            "provider": provider,
                            "model": model,
                            "function": func.__name__,
                        },
                    )
                    
                    # 记录开始
                    trace.event(
                        "function_start",
                        {"args": str(args)[:500]}
                    )
                    
                    # 执行函数
                    result = await func(*args, **kwargs)
                    
                    # 记录结束
                    duration = (time.time() - start_time) * 1000
                    trace.event(
                        "function_end",
                        {"duration_ms": duration}
                    )
                    
                    return result
                    
                except Exception as e:
                    if trace:
                        trace.event("error", {"error": str(e)})
                    raise
            
            return wrapper
        return decorator
    
    def trace_retrieval(
        self,
        name: str = "retrieval",
    ) -> Callable:
        """检索追踪装饰器"""
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                trace = langfuse_tracing.create_trace(
                    name=name,
                    metadata={"function": func.__name__},
                )
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # 记录检索结果
                    count = len(result) if result else 0
                    trace.event(
                        "retrieval_complete",
                        {
                            "count": count,
                            "duration_ms": (time.time() - start_time) * 1000
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    trace.event("error", {"error": str(e)})
                    raise
            
            return wrapper
        return decorator
    
    def trace_generation(
        self,
        name: str = "generation",
    ) -> Callable:
        """生成追踪装饰器"""
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                prompt = kwargs.get('prompt', '')
                model = kwargs.get('model', '')
                start_time = time.time()
                
                # 创建追踪
                trace = langfuse_tracing.create_trace(
                    name=name,
                    metadata={
                        "model": model,
                        "prompt_length": len(prompt),
                    },
                )
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # 记录生成
                    trace.event(
                        "generation_complete",
                        {
                            "output_length": len(result) if result else 0,
                            "duration_ms": (time.time() - start_time) * 1000
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    trace.event("error", {"error": str(e)})
                    raise
            
            return wrapper
        return decorator


# ============== 便捷函数 =============

def get_prompt(name: str, version: int = None) -> Optional[Dict]:
    """获取提示词"""
    return langfuse_tracing.get_prompt(name, version)


def create_prompt(
    name: str,
    prompt: str,
    version: int = None,
    config: Dict = None,
) -> Optional[Dict]:
    """创建提示词"""
    return langfuse_tracing.create_prompt(name, prompt, version, config)


def update_prompt(name: str, prompt: str, config: Dict = None) -> Optional[Dict]:
    """更新提示词 (自动版本管理)"""
    return langfuse_tracing.update_prompt(name, prompt, config)


def list_prompts() -> list:
    """列出所有提示词"""
    return langfuse_tracing.list_prompts()


def get_prompt_versions(name: str) -> list:
    """获取提示词版本"""
    return langfuse_tracing.get_prompt_versions(name)


def render_prompt(name: str, variables: Dict[str, str], version: int = None) -> str:
    """渲染提示词"""
    return langfuse_tracing.render_prompt(name, variables, version)


# ============== Token 统计 =============

def get_token_stats(
    start_date: datetime = None,
    end_date: datetime = None,
) -> Dict:
    """获取 Token 使用统计 (从 Langfuse)"""
    return langfuse_tracing.get_token_stats(start_date, end_date)


def get_generations(name: str = None, limit: int = 100) -> list:
    """获取生成记录"""
    return langfuse_tracing.get_generations(name, limit)


# ============== 上下文管理 =============

class TraceContext:
    """追踪上下文"""
    
    def __init__(self, name: str, metadata: Dict = None):
        self.name = name
        self.metadata = metadata or {}
        self.trace = None
    
    async def __aenter__(self):
        self.trace = langfuse_tracing.create_trace(self.name, self.metadata)
        return self.trace
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.trace:
            self.trace.end()


async def create_trace(name: str, metadata: Dict = None) -> TraceContext:
    """创建追踪上下文"""
    return TraceContext(name, metadata)


# 全局追踪器
llm_tracker = LLMTracker()
