"""集合管理 — 列表、创建、改名、删除与详情。"""
import json
from typing import TypedDict

from loguru import logger

from backend.core.bridge import Bridge, exposed
from backend.shared.chroma import ChromaManager, run_blocking
from backend.shared.embedding import embed_key, load_embed_cfg, save_embed_cfg


class Collection(TypedDict):
    name: str
    count: int
    metadata: dict[str, object]
    has_embedding: bool


class CollectionDetail(TypedDict, total=False):
    name: str
    count: int
    metadata: dict[str, object]
    error: str


class CollectionMutationResult(TypedDict, total=False):
    success: bool
    name: str
    error: str


class CollectionOpResult(TypedDict, total=False):
    success: bool
    error: str


class CollectionBridge(Bridge):

    def __init__(self, mgr: ChromaManager):
        super().__init__()
        self._mgr = mgr

    @exposed(timeout=30)
    async def list_collections(self, conn_id: str) -> list[Collection]:
        def _list():
            try:
                client = self._mgr.get_client(conn_id)
                cols = client.list_collections()
                embed_cfg = load_embed_cfg()
                result = []
                for col in cols:
                    key = embed_key(conn_id, col.name)
                    result.append({
                        "name": col.name,
                        "count": col.count(),
                        "metadata": col.metadata or {},
                        "has_embedding": bool(embed_cfg.get(key, {}).get("embedding_model")),
                    })
                return result
            except Exception as e:
                logger.error("list_collections failed: conn={} error={}", conn_id, e)
                return {"error": str(e)}

        return await run_blocking(_list)

    @exposed(timeout=30)
    async def create_collection(self, conn_id: str, name: str, metadata_json: str = '') -> CollectionMutationResult:
        def _create():
            try:
                client = self._mgr.get_client(conn_id)
                metadata = json.loads(metadata_json) if metadata_json else None
                col = client.create_collection(name=name, metadata=metadata)
                logger.info("Collection created: conn={} name={}", conn_id, name)
                return {"success": True, "name": col.name}
            except Exception as e:
                logger.error("create_collection failed: conn={} name={} error={}", conn_id, name, e)
                return {"success": False, "error": str(e)}

        return await run_blocking(_create)

    @exposed(timeout=30)
    async def modify_collection(self, conn_id: str, old_name: str, new_name: str,
                             metadata_json: str = '') -> CollectionMutationResult:
        def _modify():
            try:
                client = self._mgr.get_client(conn_id)
                col = client.get_collection(name=old_name)
                metadata = json.loads(metadata_json) if metadata_json else None
                col.modify(name=new_name, metadata=metadata)
                if old_name != new_name:
                    data = load_embed_cfg()
                    old_key = embed_key(conn_id, old_name)
                    new_key = embed_key(conn_id, new_name)
                    if old_key in data:
                        data[new_key] = data.pop(old_key)
                        save_embed_cfg(data)
                logger.info("Collection modified: conn={} {} -> {}", conn_id, old_name, new_name)
                return {"success": True, "name": new_name}
            except Exception as e:
                logger.error("modify_collection failed: conn={} name={} error={}", conn_id, old_name, e)
                return {"success": False, "error": str(e)}

        return await run_blocking(_modify)

    @exposed(timeout=30)
    async def delete_collection(self, conn_id: str, name: str) -> CollectionOpResult:
        def _delete():
            try:
                client = self._mgr.get_client(conn_id)
                client.delete_collection(name=name)
                data = load_embed_cfg()
                data.pop(embed_key(conn_id, name), None)
                save_embed_cfg(data)
                logger.info("Collection deleted: conn={} name={}", conn_id, name)
                return {"success": True}
            except Exception as e:
                logger.error("delete_collection failed: conn={} name={} error={}", conn_id, name, e)
                return {"success": False, "error": str(e)}

        return await run_blocking(_delete)

    @exposed(timeout=30)
    async def get_collection_info(self, conn_id: str, name: str) -> CollectionDetail:
        def _info():
            try:
                client = self._mgr.get_client(conn_id)
                col = client.get_collection(name=name)
                return {"name": col.name, "count": col.count(), "metadata": col.metadata or {}}
            except Exception as e:
                logger.error("get_collection_info failed: conn={} name={} error={}", conn_id, name, e)
                return {"error": str(e)}

        return await run_blocking(_info)
