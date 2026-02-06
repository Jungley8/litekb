"""
LLM 追踪装饰器
"""
import os
import time
from typing import Callable, Any, Dict, Optional
from functools import wraps
from datetime import datetime
from loguru import logger
from app.tracing.langfuse import langfuse


class TracingManager:
    """追踪管理器"""
    
    def __init__(self):
        self.traces = {}
    
    def trace_llm_call(
        self,
        name: str,
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
                    with langfuse.trace_context(
                        name=f"{name}.{func.__name__}",
                        metadata={
                            "provider": provider,
                            "model": model,
                            "function": func.__name__,
                        },
                    ) as trace:
                        # 记录函数参数
                        trace.event(
                            "function_start",
                            {"args": str(args)[:500]}
                        )
                        
                        # 执行函数
                        result = await func(*args, **kwargs)
                        
                        # 记录结果
                        trace.event(
                            "function_end",
                            {"duration_ms": (time.time() - start_time) * 1000}
                        )
                        
                        return result
                        
                except Exception as e:
                    logger.error(f"LLM call tracing failed: {e}")
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
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # 记录检索结果
                    if hasattr(result, '__len__'):
                        logger.info(
                            f"[Tracing] {name}: {len(result)} documents, "
                            f"duration: {(time.time() - start_time) * 1000:.2f}ms"
                        )
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Retrieval tracing failed: {e}")
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
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # 记录生成
                    logger.info(
                        f"[Tracing] {name}: model={model}, "
                        f"prompt_len={len(prompt)}, "
                        f"output_len={len(result) if result else 0}, "
                        f"duration: {(time.time() - start_time) * 1000:.2f}ms"
                    )
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Generation tracing failed: {e}")
                    raise
            
            return wrapper
        return decorator


# 全局追踪管理器
tracing = TracingManager()


# ============== 便捷装饰器 ==============

def trace_llm(provider: str = None, model: str = None):
    """LLM 调用追踪"""
    return tracing.trace_llm_call(
        name="llm_call",
        provider=provider,
        model=model,
    )


def trace_retrieval(name: str = "retrieval"):
    """检索追踪"""
    return tracing.trace_retrieval(name=name)


def trace_generation(name: str = "generation"):
    """生成追踪"""
    return tracing.trace_generation(name=name)


# ============== 手动追踪 =============

class TraceHelper:
    """追踪辅助类"""
    
    def __init__(self, name: str, metadata: Dict = None):
        self.name = name
        self.metadata = metadata or {}
        self.trace = None
        self.generations = []
    
    async def __aenter__(self):
        self.trace = langfuse.trace_context(
            name=self.name,
            metadata=self.metadata,
        )
        return self.trace.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.trace:
            self.trace.__exit__(exc_type, exc_val, exc_tb)
    
    def span(self, name: str, metadata: Dict = None):
        """创建跨度"""
        if self.trace:
            return self.trace.span(name=name, metadata=metadata)
        return langfuse.create_span(None, name=name, metadata=metadata)
    
    def event(self, name: str, metadata: Dict = None):
        """记录事件"""
        if self.trace:
            self.trace.event(name=name, metadata=metadata)


async def create_trace(name: str, metadata: Dict = None):
    """创建追踪"""
    helper = TraceHelper(name, metadata)
    await helper.__aenter__()
    return helper


# ============== Token 追踪 =============

class TokenTracker:
    """Token 使用追踪"""
    
    def __init__(self):
        self.tokens = {
            "total_input": 0,
            "total_output": 0,
            "total_cost": 0,
            "by_model": {},
            "by_provider": {},
        }
    
    def record_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float = None,
    ):
        """记录使用量"""
        # 按模型统计
        if model not in self.tokens["by_model"]:
            self.tokens["by_model"][model] = {
                "input": 0,
                "output": 0,
                "cost": 0,
            }
        
        self.tokens["by_model"][model]["input"] += input_tokens
        self.tokens["by_model"][model]["output"] += output_tokens
        self.tokens["by_model"][model]["cost"] += cost or 0
        
        # 按提供商统计
        if provider not in self.tokens["by_provider"]:
            self.tokens["by_provider"][provider] = {
                "input": 0,
                "output": 0,
                "cost": 0,
            }
        
        self.tokens["by_provider"][provider]["input"] += input_tokens
        self.tokens["by_provider"][provider]["output"] += output_tokens
        self.tokens["by_provider"][provider]["cost"] += cost or 0
        
        # 总计
        self.tokens["total_input"] += input_tokens
        self.tokens["total_output"] += output_tokens
        self.tokens["total_cost"] += cost or 0
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return self.tokens
    
    def reset(self):
        """重置"""
        self.tokens = {
            "total_input": 0,
            "total_output": 0,
            "total_cost": 0,
            "by_model": {},
            "by_provider": {},
        }


# 全局 Token 追踪器
token_tracker = TokenTracker()


def calculate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """计算成本 (近似)"""
    # 价格表 (每 1M tokens)
    PRICING = {
        "openai": {
            "gpt-4o": {"input": 5.0, "output": 15.0},
            "gpt-4o-mini": {"input": 0.15, "output": 0.6},
            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "text-embedding-3-small": {"input": 0.02, "output": 0},
            "text-embedding-3-large": {"input": 0.13, "output": 0},
        },
        "anthropic": {
            "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
        },
        "google": {
            "gemini-1.5-pro": {"input": 3.5, "output": 10.5},
            "gemini-1.5-flash": {"input": 0.075, "output": 0.3},
        },
    }
    
    model_pricing = PRICING.get(provider, {}).get(model, {"input": 0, "output": 0})
    
    input_cost = (input_tokens / 1_000_000) * model_pricing.get("input", 0)
    output_cost = (output_tokens / 1_000_000) * model_pricing.get("output", 0)
    
    return input_cost + output_cost
