"""
插件系统
"""

from typing import Dict, List, Any, Optional, Callable
from loguru import logger
from enum import Enum


class EventType(Enum):
    """插件事件类型"""

    # 文档事件
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"

    # 检索事件
    RETRIEVE_START = "retrieve.start"
    RETRIEVE_END = "retrieve.end"

    # 生成事件
    GENERATE_START = "generate.start"
    GENERATE_END = "generate.end"

    # 自定义事件
    CUSTOM = "custom"


class PluginHook:
    """插件钩子"""

    def __init__(self, name: str, handler: Callable):
        self.name = name
        self.handler = handler
        self.enabled = True

    async def execute(self, *args, **kwargs) -> Any:
        """执行钩子"""
        if not self.enabled:
            return None

        try:
            if callable(self.handler):
                result = self.handler(*args, **kwargs)
                if hasattr(result, "__await__"):
                    return await result
                return result
        except Exception as e:
            logger.error(f"Plugin hook error: {e}")

        return None


class PluginSystem:
    """插件系统"""

    def __init__(self):
        self.hooks: Dict[str, List[PluginHook]] = {}
        self.plugins: Dict[str, Dict] = {}

    def register_hook(
        self,
        event: str,
        handler: Callable,
        plugin_name: str = "default",
    ) -> str:
        """注册钩子"""

        hook_id = f"{plugin_name}_{event}_{id(handler)}"

        if event not in self.hooks:
            self.hooks[event] = []

        self.hooks[event].append(PluginHook(event, handler))

        logger.info(f"Registered hook: {hook_id}")
        return hook_id

    def unregister_hook(self, hook_id: str) -> bool:
        """取消注册"""

        for event, hooks in self.hooks.items():
            for i, hook in enumerate(hooks):
                if f"{hook.handler}" == hook_id or hook_id in str(hook.handler):
                    hooks.pop(i)
                    return True

        return False

    async def emit(self, event: str, *args, **kwargs) -> List[Any]:
        """触发事件"""

        results = []

        if event in self.hooks:
            for hook in self.hooks[event]:
                if hook.enabled:
                    result = await hook.execute(*args, **kwargs)
                    if result is not None:
                        results.append(result)

        return results

    def register_plugin(
        self,
        plugin_id: str,
        name: str,
        version: str = "1.0.0",
        description: str = "",
    ) -> Dict:
        """注册插件"""

        plugin = {
            "id": plugin_id,
            "name": name,
            "version": version,
            "description": description,
            "enabled": True,
            "hooks": [],
        }

        self.plugins[plugin_id] = plugin

        logger.info(f"Registered plugin: {name} v{version}")
        return plugin

    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件"""

        if plugin_id in self.plugins:
            self.plugins[plugin_id]["enabled"] = True
            return True
        return False

    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件"""

        if plugin_id in self.plugins:
            self.plugins[plugin_id]["enabled"] = False
            return True
        return False

    def get_plugins(self) -> List[Dict]:
        """获取所有插件"""
        return list(self.plugins.values())

    def get_hooks(self, event: str) -> List[PluginHook]:
        """获取事件的钩子"""
        return self.hooks.get(event, [])


# 预置钩子
class BuiltInHooks:
    """内置钩子"""

    @staticmethod
    async def sensitive_content_filter(content: str) -> str:
        """
        敏感内容过滤
        TODO: 实现敏感内容过滤
        """
        # TODO: 实现敏感内容过滤
        # 1. 检测敏感词
        # 2. 替换或标记
        return content

    @staticmethod
    async def log_hook(event: str, *args, **kwargs):
        """日志钩子"""
        logger.info(f"Event: {event}, Args: {args}, Kwargs: {kwargs}")


# 全局插件系统
plugin_system = PluginSystem()


# 钩子装饰器
def on_event(event: str):
    """事件装饰器"""

    def decorator(func: Callable):
        plugin_system.register_hook(event, func, func.__name__)
        return func

    return decorator


# 使用示例
@on_event(EventType.DOCUMENT_CREATED)
async def on_document_created(document_id: str):
    logger.info(f"Document created: {document_id}")
