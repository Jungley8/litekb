"""
异步任务队列 (Celery)
"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

# Celery 配置
celery_app = Celery(
    "litekb", broker=settings.celery_broker_url, backend=settings.celery_result_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


# ==================== 任务定义 ====================


@celery_app.task(bind=True, max_retries=3)
def process_document(self, doc_id: str, kb_id: str):
    """
    处理文档 (异步)
    - 解析文档
    - 分块
    - 生成向量
    - 构建图谱
    """
    from app.services.document import document_service
    from app.services.vector import vector_store
    from app.services.graph import graph_service

    try:
        # 1. 获取文档
        from app.models_v2 import get_session, Document

        session = get_session()
        doc = session.query(Document).get(doc_id)

        if not doc:
            return {"error": "Document not found"}

        # 2. 解析文档
        doc.status = "processing"
        session.commit()

        # 3. 分块并索引
        chunks = document_service.split_chunks(doc.content or "")

        # 4. 生成向量
        if chunks:
            embeddings = await vector_store.get_embeddings([c.content for c in chunks])
            await vector_store.add_chunks(kb_id, chunks, embeddings)

        # 5. 构建知识图谱
        if doc.content:
            await graph_service.build_graph(kb_id, doc_id, doc.content[:10000])

        # 6. 更新状态
        doc.status = "indexed"
        doc.metadata["chunk_count"] = len(chunks)
        session.commit()

        return {"doc_id": doc_id, "chunks_count": len(chunks), "status": "completed"}

    except Exception as e:
        doc.status = "failed"
        doc.metadata["error"] = str(e)
        session.commit()

        raise self.retry(exc=e, countdown=60)


@celery_app.task
def index_documents(kb_id: str, doc_ids: list):
    """批量索引文档"""
    for doc_id in doc_ids:
        process_document.delay(doc_id, kb_id)

    return {"queued": len(doc_ids)}


@celery_app.task
def rebuild_knowledge_graph(kb_id: str):
    """
    重建知识图谱 (定时任务)
    """
    from app.services.graph import graph_service

    # 获取所有文档
    from app.models_v2 import get_session, Document

    session = get_session()
    docs = (
        session.query(Document)
        .filter(Document.kb_id == kb_id, Document.status == "indexed")
        .all()
    )

    stats = {"entities": 0, "relations": 0}

    for doc in docs:
        result = await graph_service.build_graph(kb_id, doc.id, doc.content[:10000])
        stats["entities"] += result["entities"]
        stats["relations"] += result["relations"]

    return stats


@celery_app.task
def cleanup_expired_keys():
    """
    清理过期 API Key
    """
    from app.models_v2 import get_session, APIKey
    from datetime import datetime

    session = get_session()
    expired = (
        session.query(APIKey)
        .filter(APIKey.expires_at < datetime.utcnow(), APIKey.is_active == True)
        .update({"is_active": False})
    )

    session.commit()

    return {"cleaned": expired}


@celery_app.task
def generate_weekly_report(org_id: str):
    """
    生成周报 (定时任务)
    """
    # TODO: 实现报告生成
    return {"org_id": org_id, "status": "generated"}


# ==================== Celery Beat 定时任务 ====================

celery_app.conf.beat_schedule = {
    # 每天凌晨清理过期 Key
    "cleanup-expired-keys": {
        "task": "cleanup_expired_keys",
        "schedule": crontab(hour=0, minute=0),
    },
    # 每周日重建图谱
    "rebuild-graphs": {
        "task": "rebuild_knowledge_graph",
        "schedule": crontab(day_of_week="sun", hour=2, minute=0),
        "args": ["default"],  # 默认知识库
    },
    # 每周一生成周报
    "weekly-report": {
        "task": "generate_weekly_report",
        "schedule": crontab(day_of_week="mon", hour=9, minute=0),
    },
}


# ==================== 任务工具 ====================


def run_task(task_name: str, **kwargs):
    """触发任务"""
    task = celery_app.send_task(task_name, kwargs=kwargs)
    return task.id


def get_task_result(task_id: str):
    """获取任务结果"""
    result = celery_app.AsyncResult(task_id)
    return {
        "id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
