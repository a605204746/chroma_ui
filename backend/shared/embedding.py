"""集合级 embedding（OpenAI 兼容）配置的持久化与调用。

配置文件位于 ~/.chroma_walnut_ui/collection_embeddings.json，
key 为 "{conn_id}:{collection}"。
"""
import json
import urllib.request
from pathlib import Path

EMBED_CFG_PATH = Path.home() / ".chroma_walnut_ui" / "collection_embeddings.json"


def load_embed_cfg() -> dict:
    if EMBED_CFG_PATH.exists():
        return json.loads(EMBED_CFG_PATH.read_text(encoding="utf-8"))
    return {}


def save_embed_cfg(data: dict) -> None:
    EMBED_CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    EMBED_CFG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def embed_key(conn_id: str, collection: str) -> str:
    return f"{conn_id}:{collection}"


def get_collection_embed_cfg(conn_id: str, collection: str) -> dict:
    return load_embed_cfg().get(embed_key(conn_id, collection), {})


def call_embedding(conn_id: str, collection: str, text: str) -> list:
    """调用集合配置的 OpenAI 兼容 embedding 接口；未配置时返回空列表。"""
    cfg = get_collection_embed_cfg(conn_id, collection)
    url = cfg.get("embedding_url", "")
    model = cfg.get("embedding_model", "")
    api_key = cfg.get("embedding_api_key", "")
    if not url or not model:
        return []
    payload = json.dumps({"model": model, "input": text}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["data"][0]["embedding"]
