"""集合级 embedding 配置 — OpenAI 兼容接口配置的读写、测试与维度探测。"""
from typing import TypedDict

from loguru import logger

from backend.core.bridge import Bridge, exposed
from backend.shared.chroma import ChromaManager, run_blocking
from backend.shared.embedding import (
    call_embedding,
    embed_key,
    get_collection_embed_cfg,
    load_embed_cfg,
    save_embed_cfg,
)


class _EmbeddingCfgBase(TypedDict):
    embedding_url: str
    embedding_model: str
    embedding_api_key: str


class EmbeddingConfig(_EmbeddingCfgBase, total=False):
    dimension: int


class EmbeddingOpResult(TypedDict):
    success: bool


class TestEmbeddingResult(TypedDict, total=False):
    dimension: int
    preview: list[float]
    error: str


class EmbeddingInfo(TypedDict, total=False):
    dimension: int | None
    error: str


class EmbeddingBridge(Bridge):

    def __init__(self, mgr: ChromaManager):
        super().__init__()
        self._mgr = mgr

    @exposed
    async def get_collection_embedding(self, conn_id: str, collection: str) -> EmbeddingConfig:
        return get_collection_embed_cfg(conn_id, collection)

    @exposed
    async def set_collection_embedding(self, conn_id: str, collection: str,
                                       embedding_url: str, embedding_model: str,
                                       embedding_api_key: str, dimension: int = 0) -> EmbeddingOpResult:
        data = load_embed_cfg()
        data[embed_key(conn_id, collection)] = {
            "embedding_url": embedding_url,
            "embedding_model": embedding_model,
            "embedding_api_key": embedding_api_key,
            "dimension": dimension or 0,
        }
        save_embed_cfg(data)
        logger.info("Embedding config saved: conn={} collection={} model={}", conn_id, collection, embedding_model)
        return {"success": True}

    @exposed
    async def clear_collection_embedding(self, conn_id: str, collection: str) -> EmbeddingOpResult:
        data = load_embed_cfg()
        data.pop(embed_key(conn_id, collection), None)
        save_embed_cfg(data)
        logger.info("Embedding config cleared: conn={} collection={}", conn_id, collection)
        return {"success": True}

    @exposed(timeout=60)
    async def test_embedding(self, conn_id: str, collection: str, text: str) -> TestEmbeddingResult:
        def _test():
            try:
                emb = call_embedding(conn_id, collection, text)
                if not emb:
                    return {"error": "未配置嵌入模型"}
                return {"dimension": len(emb), "preview": [round(v, 6) for v in emb[:5]]}
            except Exception as e:
                logger.error("test_embedding failed: conn={} collection={} error={}", conn_id, collection, e)
                return {"error": str(e)}

        return await run_blocking(_test)

    @exposed(timeout=30)
    async def get_embedding_info(self, conn_id: str, collection: str) -> EmbeddingInfo:
        def _info():
            try:
                client = self._mgr.get_client(conn_id)
                col = client.get_collection(name=collection)
                result = col.get(limit=1, include=["embeddings"])
                embeddings = result.get("embeddings")
                if embeddings is None or len(embeddings) == 0:
                    return {"dimension": None}
                first = embeddings[0]
                if first is None:
                    return {"dimension": None}
                return {"dimension": int(len(first))}
            except Exception as e:
                logger.error("get_embedding_info failed: conn={} collection={} error={}", conn_id, collection, e)
                return {"error": str(e), "dimension": None}

        return await run_blocking(_info)
