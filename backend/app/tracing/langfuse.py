"""
Langfuse 提示词管理与 Token 统计
"""
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger


class LangfuseTracing:
    """Langfuse 追踪 - 原生 API 实现"""
    
    def __init__(self):
        self._client = None
        self._enabled = False
        self._init_client()
    
    def _init_client(self):
        """初始化 Langfuse 客户端"""
        self._enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
        
        if not self._enabled:
            logger.info("Langfuse disabled")
            return
        
        try:
            from langfuse import Langfuse
            from langfuse.decorators import langfuse_context
            
            self._client = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
            
            logger.info("Langfuse initialized")
            
        except ImportError:
            logger.warning("langfuse not installed")
            self._enabled = False
        
        except Exception as e:
            logger.warning(f"Langfuse init failed: {e}")
            self._enabled = False
    
    @property
    def client(self):
        return self._client
    
    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None
    
    # ============== 提示词管理 ==============
    
    def get_prompt(self, name: str, version: int = None) -> Optional[Dict]:
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
        """创建提示词"""
        if not self.enabled:
            return None
        
        try:
            langfuse_prompt = self._client.create_prompt(
                name=name,
                prompt=prompt,
                version=version,
                config=config or {},
            )
            return {
                "name": langfuse_prompt.name,
                "prompt": langfuse_prompt.prompt,
                "version": langfuse_prompt.version,
            }
        except Exception as e:
            logger.warning(f"Create prompt failed: {e}")
            return None
    
    def update_prompt(
        self,
        name: str,
        prompt: str,
        config: Dict = None,
    ) -> Optional[Dict]:
        """更新提示词"""
        if not self.enabled:
            return None
        
        try:
            # Langfuse 自动管理版本
            langfuse_prompt = self._client.create_prompt(
                name=name,
                prompt=prompt,
                config=config or {},
            )
            return {
                "name": langfuse_prompt.name,
                "prompt": langfuse_prompt.prompt,
                "version": langfuse_prompt.version,
            }
        except Exception as e:
            logger.warning(f"Update prompt failed: {e}")
            return None
    
    def list_prompts(self) -> List[Dict]:
        """列出所有提示词"""
        if not self.enabled:
            return []
        
        try:
            prompts = self._client.get_prompts()
            return [
                {
                    "name": p.name,
                    "version": p.version,
                    "created_at": p.created_at.isoformat() if hasattr(p.created_at, 'isoformat') else str(p.created_at),
                }
                for p in prompts.data
            ]
        except Exception as e:
            logger.warning(f"List prompts failed: {e}")
            return []
    
    def get_prompt_versions(self, name: str) -> List[Dict]:
        """获取提示词版本历史"""
        if not self.enabled:
            return []
        
        try:
            prompt = self._client.get_prompt(name=name)
            versions = []
            
            # Langfuse 限制获取所有版本
            for v in [prompt.version]:
                versions.append({
                    "version": v,
                    "prompt": prompt.prompt,
                })
            
            return versions
        except Exception as e:
            logger.warning(f"Get versions failed: {e}")
            return []
    
    def render_prompt(
        self,
        name: str,
        variables: Dict[str, str],
        version: int = None,
    ) -> str:
        """渲染提示词"""
        prompt_data = self.get_prompt(name, version)
        if not prompt_data:
            return ""
        
        rendered = prompt_data["prompt"]
        
        # 替换变量
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
            rendered = rendered.replace(f"${{{key}}}", str(value))
        
        return rendered
    
    def delete_prompt(self, name: str, version: int) -> bool:
        """删除提示词版本"""
        # Langfuse API 不支持删除，返回 False
        logger.warning("Langfuse API doesn't support prompt deletion")
        return False
    
    # ============== Tracing ==============
    
    def create_trace(
        self,
        name: str,
        metadata: Dict = None,
        user_id: str = None,
    ):
        """创建追踪"""
        if not self.enabled:
            return LocalTrace(name, metadata)
        
        try:
            from langfuse import LangfuseTrace
            trace = self._client.trace(
                name=name,
                metadata=metadata,
                user_id=user_id,
            )
            return LangfuseTraceObj(trace)
        except Exception as e:
            logger.warning(f"Create trace failed: {e}")
            return LocalTrace(name, metadata)
    
    def create_generation(
        self,
        trace,
        name: str,
        prompt: str,
        model: str,
        completion: str = None,
        usage: Dict = None,
        metadata: Dict = None,
    ):
        """创建生成记录 (含 Token 统计)"""
        if not self.enabled:
            return LocalGeneration(name, prompt, model, completion)
        
        try:
            from langfuse import LangfuseGeneration
            generation = trace.generation(
                name=name,
                input=prompt,
                model=model,
                output=completion,
                metadata=metadata,
                usage=usage,
            )
            return LangfuseGenerationObj(generation, usage)
        except Exception as e:
            logger.warning(f"Create generation failed: {e}")
            return LocalGeneration(name, prompt, model, completion)
    
    def create_span(
        self,
        trace,
        name: str,
        metadata: Dict = None,
    ):
        """创建跨度"""
        if not self.enabled:
            return LocalSpan(name, metadata)
        
        try:
            from langfuse import LangfuseSpan
            span = trace.span(
                name=name,
                metadata=metadata,
            )
            return LangfuseSpanObj(span)
        except Exception as e:
            logger.warning(f"Create span failed: {e}")
            return LocalSpan(name, metadata)
    
    # ============== Token & Cost 统计 ==============
    
    def get_generations(
        self,
        name: str = None,
        limit: int = 100,
    ) -> List[Dict]:
        """获取生成记录 (Token 统计)"""
        if not self.enabled:
            return []
        
        try:
            from datetime import timedelta
            
            generations = self._client.generations(
                name=name,
                limit=limit,
            )
            
            return [
                {
                    "name": g.name,
                    "model": g.model,
                    "input_tokens": g.usage.input_tokens if g.usage else 0,
                    "output_tokens": g.usage.output_tokens if g.usage else 0,
                    "total_tokens": (g.usage.input_tokens + g.usage.output_tokens) if g.usage else 0,
                    "cost": g.usage.calculated_cost if g.usage else 0,
                    "created_at": g.created_at.isoformat() if hasattr(g.created_at, 'isoformat') else str(g.created_at),
                }
                for g in generations.data
            ]
        except Exception as e:
            logger.warning(f"Get generations failed: {e}")
            return []
    
    def get_token_stats(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Dict:
        """获取 Token 使用统计"""
        if not self.enabled:
            return {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "by_model": {},
                "by_day": {},
            }
        
        try:
            generations = self.get_generations(limit=1000)
            
            stats = {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "by_model": {},
                "by_day": {},
            }
            
            for g in generations:
                input_t = g.get("input_tokens", 0)
                output_t = g.get("output_tokens", 0)
                cost = g.get("cost", 0)
                model = g.get("model", "unknown")
                created = g.get("created_at", "")
                
                # 更新总计
                stats["total_input_tokens"] += input_t
                stats["total_output_tokens"] += output_t
                stats["total_tokens"] += input_t + output_t
                stats["total_cost"] += cost
                
                # 按模型统计
                if model not in stats["by_model"]:
                    stats["by_model"][model] = {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cost": 0,
                    }
                stats["by_model"][model]["input_tokens"] += input_t
                stats["by_model"][model]["output_tokens"] += output_t
                stats["by_model"][model]["cost"] += cost
            
            return stats
            
        except Exception as e:
            logger.warning(f"Get token stats failed: {e}")
            return {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "by_model": {},
                "by_day": {},
            }


# ============== 本地回退类 ==============

class LocalTrace:
    """本地追踪"""
    def __init__(self, name: str, metadata: Dict = None):
        self.name = name
        self.metadata = metadata or {}
        self.generations = []
        self.spans = []
        self.events = []
    
    def generation(self, **kwargs):
        gen = LocalGeneration(
            name=kwargs.get("name", "gen"),
            prompt=kwargs.get("input", ""),
            model=kwargs.get("model", ""),
        )
        self.generations.append(gen)
        return gen
    
    def span(self, **kwargs):
        span = LocalSpan(kwargs.get("name", "span"))
        self.spans.append(span)
        return span
    
    def event(self, name: str, metadata: Dict = None):
        self.events.append({"name": name, "metadata": metadata})
    
    def end(self, metadata: Dict = None):
        pass


class LocalGeneration:
    """本地生成"""
    def __init__(self, name: str, prompt: str, model: str, completion: str = None):
        self.name = name
        self.prompt = prompt
        self.model = model
        self.completion = completion
        self.usage = {}
    
    def end(self, **kwargs):
        self.usage = kwargs.get("usage", {})


class LocalSpan:
    """本地跨度"""
    def __init__(self, name: str, metadata: Dict = None):
        self.name = name
        self.metadata = metadata or {}
        self.events = []
    
    def event(self, name: str, metadata: Dict = None):
        self.events.append({"name": name, "metadata": metadata})
    
    def end(self, **kwargs):
        pass


# ============== Langfuse 包装类 ==============

class LangfuseTraceObj:
    """Langfuse 追踪包装"""
    def __init__(self, trace):
        self._trace = trace
    
    def generation(self, **kwargs):
        from langfuse import LangfuseGeneration
        return LangfuseGenerationObj(
            self._trace.generation(**kwargs),
            kwargs.get("usage")
        )
    
    def span(self, **kwargs):
        from langfuse import LangfuseSpan
        return LangfuseSpanObj(self._trace.span(**kwargs))
    
    def event(self, name: str, metadata: Dict = None):
        self._trace.event(name=name, metadata=metadata)
    
    def end(self, metadata: Dict = None):
        self._trace.end(metadata=metadata)


class LangfuseGenerationObj:
    """Langfuse 生成包装"""
    def __init__(self, generation, usage: Dict = None):
        self._gen = generation
        self._usage = usage or {}
    
    def end(self, **kwargs):
        output = kwargs.get("output")
        usage = kwargs.get("usage") or self._usage
        self._gen.end(output=output, usage=usage)
    
    @property
    def usage(self):
        return self._usage


class LangfuseSpanObj:
    """Langfuse 跨度包装"""
    def __init__(self, span):
        self._span = span
    
    def event(self, name: str, metadata: Dict = None):
        self._span.event(name=name, metadata=metadata)
    
    def end(self, **kwargs):
        self._span.end(**kwargs)


# 全局实例
langfuse_tracing = LangfuseTracing()
