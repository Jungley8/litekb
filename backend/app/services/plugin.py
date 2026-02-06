"""
插件系统
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from loguru import logger
from functools import wraps
import importlib
import inspect


class PluginHook(str, Enum):
    """插件钩子"""
    # 文档处理
    DOCUMENT_BEFORE_UPLOAD = "document:before_upload"
    DOCUMENT_AFTER_UPLOAD = "document:after_upload"
    DOCUMENT_BEFORE_PARSE = "document:before_parse"
    DOCUMENT_AFTER_PARSE = "document:after_parse"
    
    # 搜索
    SEARCH_BEFORE_QUERY = "search:before_query"
    SEARCH_AFTER_QUERY = "search:after_query"
    SEARCH_RANKING = "search:ranking"
    
    # RAG
    RAG_BEFORE_RETRIEVE = "rag:before_retrieve"
    RAG_AFTER_RETRIEVE = "rag:after_retrieve"
    RAG_BEFORE_GENERATE = "rag:before_generate"
    RAG_AFTER_GENERATE = "rag:after_generate"
    
    # 图谱
    GRAPH_EXTRACT_ENTITIES = "graph:extract_entities"
    GRAPH_EXTRACT_RELATIONS = "graph:extract_relations"
    
    # 用户
    USER_LOGIN = "user:login"
    USER_REGISTER = "user:register"


@dataclass
class PluginInfo:
    """插件信息"""
    id: str
    name: str
    version: str
    author: str
    description: str
    hooks: List[str]
    enabled: bool = True


@dataclass
class PluginContext:
    """插件执行上下文"""
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginBase(ABC):
    """插件基类"""
    
    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """插件信息"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]):
        """初始化插件"""
        pass
    
    def before_load(self):
        """加载前"""
        pass
    
    def after_load(self):
        """加载后"""
        pass
    
    def before_unload(self):
        """卸载前"""
        pass


class Plugin:
    """插件"""
    
    def __init__(self):
        self.hooks: Dict[str, List[Callable]] = {}
        self.plugins: Dict[str, PluginBase] = {}
    
    def register_hook(self, hook: str):
        """注册钩子装饰器"""
        def decorator(func: Callable):
            if hook not in self.hooks:
                self.hooks[hook] = []
            self.hooks[hook].append(func)
            return func
        return decorator
    
    def add_plugin(self, plugin: PluginBase):
        """添加插件"""
        self.plugins[plugin.info.id] = plugin
        logger.info(f"Plugin loaded: {plugin.info.name}")
    
    def remove_plugin(self, plugin_id: str):
        """移除插件"""
        if plugin_id in self.plugins:
            self.plugins[plugin_id].before_unload()
            del self.plugins[plugin_id]
            logger.info(f"Plugin unloaded: {plugin_id}")
    
    async def execute_hook(
        self,
        hook: str,
        context: PluginContext
    ) -> PluginContext:
        """执行钩子"""
        if hook not in self.hooks:
            return context
        
        for func in self.hooks[hook]:
            try:
                if asyncio.iscoroutinefunction(func):
                    context = await func(context)
                else:
                    context = func(context)
            except Exception as e:
                logger.error(f"Hook {hook} failed: {e}")
                # 继续执行其他钩子
        
        return context
    
    def get_registered_hooks(self) -> Dict[str, int]:
        """获取已注册的钩子"""
        return {hook: len(funcs) for hook, funcs in self.hooks.items()}


# 全局插件管理器
plugin_manager = Plugin()


# ==================== 常用钩子 ====================

def hook(hook_name: PluginHook):
    """钩子装饰器"""
    def decorator(func: Callable):
        plugin_manager.register_hook(hook_name.value)(func)
        return func
    return decorator


# ==================== 内置插件 = ====================

class AnalyticsPlugin(PluginBase):
    """分析插件 - 记录使用统计"""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            id="analytics",
            name="使用分析",
            version="1.0.0",
            author="LiteKB",
            description="记录使用统计数据",
            hooks=[
                PluginHook.DOCUMENT_AFTER_UPLOAD.value,
                PluginHook.RAG_AFTER_GENERATE.value,
            ]
        )
    
    def initialize(self, config: Dict[str, Any]):
        self.config = config
    
    @hook(PluginHook.DOCUMENT_AFTER_UPLOAD)
    def track_upload(self, context: PluginContext):
        logger.info(f"Document uploaded: {context.data.get('doc_id')}")
        return context
    
    @hook(PluginHook.RAG_AFTER_GENERATE)
    def track_rag(self, context: PluginContext):
        logger.info(f"RAG query: {context.data.get('question')}")
        return context


class SecurityPlugin(PluginBase):
    """安全插件 - 内容过滤"""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            id="security",
            name="安全过滤",
            version="1.0.0",
            author="LiteKB",
            description="敏感内容过滤",
            hooks=[
                PluginHook.DOCUMENT_BEFORE_PARSE.value,
                PluginHook.RAG_BEFORE_GENERATE.value,
            ]
        )
    
    def initialize(self, config: Dict[str, Any]):
        self.config = config
    
    @hook(PluginHook.DOCUMENT_BEFORE_PARSE)
    def scan_content(self, context: PluginContext):
        content = context.data.get("content", "")
        # TODO: 实现敏感内容过滤
        return context


# ==================== 插件 API ====================

class PluginAPI:
    """插件 API"""
    
    @staticmethod
    def register_document_processor(
        processor_id: str,
        extensions: List[str],
        handler: Callable
    ):
        """注册文档处理器"""
        # TODO: 实现处理器注册
        logger.info(f"Registered document processor: {processor_id}")
    
    @staticmethod
    def register_llm_provider(
        provider_id: str,
        name: str,
        handler: Callable
    ):
        """注册 LLM 提供商"""
        # TODO: 实现提供商注册
        logger.info(f"Registered LLM provider: {provider_id}")
    
    @staticmethod
    def register_search_backend(
        backend_id: str,
        name: str,
        handler: Callable
    ):
        """注册搜索后端"""
        # TODO: 实现搜索后端注册
        logger.info(f"Registered search backend: {backend_id}")


# 全局插件 API
plugin_api = PluginAPI()


# ==================== 插件管理 ====================

class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugin_dir = "plugins"
        self.loaded_plugins: Dict[str, PluginBase] = {}
    
    def load_plugin(self, plugin_path: str) -> bool:
        """加载插件"""
        try:
            # 动态导入
            spec = importlib.util.spec_from_file_location(
                "plugin", plugin_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 获取插件类
            if hasattr(module, 'get_plugin'):
                plugin_class = module.get_plugin()
            else:
                return False
            
            # 实例化并加载
            plugin = plugin_class()
            plugin.before_load()
            plugin.initialize({})
            plugin.after_load()
            
            self.loaded_plugins[plugin.info.id] = plugin
            plugin_manager.add_plugin(plugin)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_path}: {e}")
            return False
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        if plugin_id in self.loaded_plugins:
            plugin_manager.remove_plugin(plugin_id)
            del self.loaded_plugins[plugin_id]
            return True
        return False
    
    def list_plugins(self) -> List[PluginInfo]:
        """列出插件"""
        return [
            plugin.info for plugin in self.loaded_plugins.values()
        ]
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件"""
        if plugin_id in self.loaded_plugins:
            self.loaded_plugins[plugin_id].info.enabled = True
            return True
        return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件"""
        if plugin_id in self.loaded_plugins:
            self.loaded_plugins[plugin_id].info.enabled = False
            return True
        return False


# 全局实例
plugin_svc = PluginManager()
