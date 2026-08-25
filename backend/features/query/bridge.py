"""向量查询 — 按文本（自动走集合配置的 embedding 接口）或 where 过滤查询。"""
import json
from typing import TypedDict

from loguru import logger

from backend.core.bridge import Bridge, exposed
from backend.shared.chroma import ChromaManager, run_blocking
from backend.shared.embedding import call_embedding


class QueryResultItem(TypedDict):
    id: str
    document: str
    metadata: dict[str, object]
    distance: float | None


class QueryResult(TypedDict, total=False):
    items: list[QueryResultItem]
    error: str


class QueryBridge(Bridge):

    def __init__(self, mgr: ChromaManager):
        super().__init__()
        self._mgr = mgr

    @exposed(timeout=60)
    async def query(self, conn_id: str, collection: str, query_text: str,
                    n_results: int, where_json: str) -> QueryResult:
        def _query():
            try:
                client = self._mgr.get_client(conn_id)
                col = client.get_collection(name=collection)
                kwargs: dict = {
                    "n_results": int(n_results),
                    "include": ["documents", "metadatas", "distances"],
                }
                emb = call_embedding(conn_id, collection, query_text)
                if emb:
                    kwargs["query_embeddings"] = [emb]
                else:
                    kwargs["query_texts"] = [query_text]
                if where_json:
                    kwargs["where"] = json.loads(where_json)
                result = col.query(**kwargs)
                items = []
                ids = result["ids"][0]
                docs = result["documents"][0] if result["documents"] else []
                metas = result["metadatas"][0] if result["metadatas"] else []
                dists = result["distances"][0] if result["distances"] else []
                for i, doc_id in enumerate(ids):
                    raw_meta = metas[i] if i < len(metas) else None
                    items.append({
                        "id": doc_id,
                        "document": docs[i] if i < len(docs) else "",
                        "metadata": raw_meta or {},
                        "distance": dists[i] if i < len(dists) else None,
                    })
                logger.info("Query executed: conn={} collection={} n_results={}", conn_id, collection, n_results)
                return {"items": items}
            except Exception as e:
                logger.error("query failed: conn={} collection={} error={}", conn_id, collection, e)
                return {"error": str(e)}

        return await run_blocking(_query)
