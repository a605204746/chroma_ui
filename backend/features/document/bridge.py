"""文档管理 — 分页读取、增删改与种子测试数据。"""
import json
import uuid
from typing import TypedDict

from loguru import logger

from backend.core.bridge import Bridge, exposed
from backend.shared.chroma import ChromaManager, run_blocking
from backend.shared.embedding import call_embedding


class _DocumentBase(TypedDict):
    id: str
    document: str
    metadata: dict[str, object]


class DocumentWithEmbedding(_DocumentBase, total=False):
    embedding: list[float] | None


class DocumentsResult(TypedDict, total=False):
    total: int
    items: list[DocumentWithEmbedding]
    error: str


class DocumentOpResult(TypedDict, total=False):
    success: bool
    error: str


class SeedResult(TypedDict, total=False):
    success: bool
    count: int
    error: str


_SEED_DOCS = [
    ("人工智能正在改变我们的生活方式，从智能家居到自动驾驶，无处不在。", "tech", 1),
    ("深度学习是机器学习的一个子领域，通过多层神经网络来学习数据的表示。", "tech", 2),
    ("自然语言处理让计算机能够理解和生成人类语言，是AI的重要分支。", "tech", 3),
    ("向量数据库专门用于存储和检索高维向量数据，是RAG系统的核心组件。", "tech", 4),
    ("大语言模型通过海量文本数据训练，能够执行各种语言理解和生成任务。", "tech", 5),
    ("Python是数据科学和机器学习领域最流行的编程语言之一。", "tech", 6),
    ("云计算的兴起让企业可以按需使用计算资源，大大降低了IT成本。", "tech", 7),
    ("区块链技术通过去中心化的方式保证数据的不可篡改性和透明性。", "tech", 8),
    ("量子计算利用量子力学原理，有望在特定问题上超越传统计算机。", "tech", 9),
    ("边缘计算将数据处理移至靠近数据源的位置，降低延迟并减轻云端压力。", "tech", 10),
    ("气候变化是当今世界面临的最严峻挑战之一，需要全球共同应对。", "science", 11),
    ("太阳能和风能等可再生能源正在快速替代传统化石燃料。", "science", 12),
    ("CRISPR基因编辑技术为治疗遗传性疾病带来了革命性的可能性。", "science", 13),
    ("黑洞是宇宙中密度极大的天体，连光也无法逃脱其引力。", "science", 14),
    ("疫苗的发明是人类医学史上最重要的成就之一，拯救了数十亿人的生命。", "science", 15),
    ("纳米技术在医疗、材料和电子领域展现出巨大的应用潜力。", "science", 16),
    ("海洋占地球表面积的71%，但人类对深海的探索仍然十分有限。", "science", 17),
    ("脑机接口技术正在帮助瘫痪患者重新获得与外界沟通的能力。", "science", 18),
    ("干细胞研究为再生医学开辟了新的道路，有望修复受损器官。", "science", 19),
    ("天文学家发现越来越多的系外行星，其中一些可能适合生命存在。", "science", 20),
    ("唐朝是中国历史上最繁荣的时期之一，文化艺术达到了新的高峰。", "history", 21),
    ("丝绸之路连接了东西方文明，促进了贸易、文化和知识的交流。", "history", 22),
    ("工业革命从英国开始，彻底改变了人类的生产方式和社会结构。", "history", 23),
    ("古罗马帝国的法律体系对现代西方法律产生了深远的影响。", "history", 24),
    ("郑和下西洋是人类历史上规模最大的航海探险活动之一。", "history", 25),
    ("文艺复兴运动重新发现了古典文化，推动了科学和艺术的蓬勃发展。", "history", 26),
    ("第二次世界大战是人类历史上最具破坏性的武装冲突，深刻改变了世界格局。", "history", 27),
    ("古埃及文明以其宏伟的金字塔和精密的天文历法而闻名于世。", "history", 28),
    ("印刷术的发明极大地推动了知识的传播和文艺复兴的到来。", "history", 29),
    ("冷战期间，美苏两国的太空竞赛推动了人类航天技术的飞速发展。", "history", 30),
    ("冥想和正念练习有助于减轻压力、改善注意力和提升整体幸福感。", "lifestyle", 31),
    ("均衡饮食和规律运动是维持健康生活方式的两大基石。", "lifestyle", 32),
    ("阅读不仅能增长知识，还能提升同理心和创造性思维能力。", "lifestyle", 33),
    ("良好的睡眠习惯对身体健康和认知功能至关重要。", "lifestyle", 34),
    ("旅行能拓宽视野，让人更好地理解不同文化和生活方式。", "lifestyle", 35),
    ("园艺不仅是一种休闲活动，还有助于减轻焦虑和改善心理健康。", "lifestyle", 36),
    ("学习一门新语言可以延缓认知退化并增强大脑的可塑性。", "lifestyle", 37),
    ("志愿服务能增强社区凝聚力，同时也给志愿者带来满足感和幸福感。", "lifestyle", 38),
    ("数字排毒帮助人们减少对屏幕的依赖，找回现实生活中的专注力。", "lifestyle", 39),
    ("烹饪自己的食物不仅更健康，也是一种创造性的自我表达方式。", "lifestyle", 40),
    ("全球化使各国经济深度融合，既带来机遇也带来新的挑战。", "economy", 41),
    ("数字货币的兴起正在重塑传统金融体系和支付方式。", "economy", 42),
    ("电商的普及彻底改变了零售业的商业模式和消费者行为。", "economy", 43),
    ("碳排放交易市场是通过市场机制应对气候变化的重要手段。", "economy", 44),
    ("人口老龄化是许多发达国家面临的共同挑战，影响社会保障和劳动力市场。", "economy", 45),
    ("共享经济模式通过平台连接闲置资源与需求方，提高了资源利用效率。", "economy", 46),
    ("供应链管理的优化对于提升企业竞争力和应对全球风险至关重要。", "economy", 47),
    ("绿色经济倡导在经济发展的同时保护环境，实现可持续增长。", "economy", 48),
    ("创业生态系统的繁荣需要资本、人才、政策和文化的共同支撑。", "economy", 49),
    ("数据已成为21世纪最重要的生产要素，驱动着新经济的发展。", "economy", 50),
]


class DocumentBridge(Bridge):

    def __init__(self, mgr: ChromaManager):
        super().__init__()
        self._mgr = mgr

    @exposed(timeout=30)
    async def get_documents(self, conn_id: str, collection: str, limit: int = 20,
                            offset: int = 0, include_embeddings: bool = False) -> DocumentsResult:
        def _get():
            try:
                client = self._mgr.get_client(conn_id)
                col = client.get_collection(name=collection)
                total = col.count()
                includes = ["documents", "metadatas"]
                if include_embeddings:
                    includes.append("embeddings")
                result = col.get(limit=int(limit), offset=int(offset), include=includes)
                embeddings = result.get("embeddings")
                items = []
                for i, doc_id in enumerate(result["ids"]):
                    emb = None
                    if embeddings is not None and i < len(embeddings) and embeddings[i] is not None:
                        emb = [round(float(v), 6) for v in embeddings[i]]
                    raw_meta = result["metadatas"][i] if result["metadatas"] else None
                    items.append({
                        "id": doc_id,
                        "document": result["documents"][i] if result["documents"] else "",
                        "metadata": raw_meta or {},
                        "embedding": emb,
                    })
                return {"total": total, "items": items}
            except Exception as e:
                logger.error("get_documents failed: conn={} collection={} error={}", conn_id, collection, e)
                return {"error": str(e)}

        return await run_blocking(_get)

    @exposed(timeout=60)
    async def add_document(self, conn_id: str, collection: str, doc_id: str,
                           document: str, metadata_json: str) -> DocumentOpResult:
        def _add():
            try:
                client = self._mgr.get_client(conn_id)
                col = client.get_collection(name=collection)
                metadata = json.loads(metadata_json) if metadata_json else {}
                kwargs: dict = {"ids": [doc_id], "documents": [document]}
                if metadata:
                    kwargs["metadatas"] = [metadata]
                emb = call_embedding(conn_id, collection, document)
                if emb:
                    kwargs["embeddings"] = [emb]
                col.add(**kwargs)
                logger.info("Document added: conn={} collection={} id={}", conn_id, collection, doc_id)
                return {"success": True}
            except Exception as e:
                logger.error("add_document failed: conn={} collection={} id={} error={}", conn_id, collection, doc_id, e)
                return {"success": False, "error": str(e)}

        return await run_blocking(_add)

    @exposed(timeout=60)
    async def update_document(self, conn_id: str, collection: str, doc_id: str,
                              document: str, metadata_json: str) -> DocumentOpResult:
        def _update():
            try:
                client = self._mgr.get_client(conn_id)
                col = client.get_collection(name=collection)
                metadata = json.loads(metadata_json) if metadata_json else {}
                kwargs: dict = {"ids": [doc_id], "documents": [document]}
                if metadata:
                    kwargs["metadatas"] = [metadata]
                emb = call_embedding(conn_id, collection, document)
                if emb:
                    kwargs["embeddings"] = [emb]
                col.update(**kwargs)
                logger.info("Document updated: conn={} collection={} id={}", conn_id, collection, doc_id)
                return {"success": True}
            except Exception as e:
                logger.error("update_document failed: conn={} collection={} id={} error={}", conn_id, collection, doc_id, e)
                return {"success": False, "error": str(e)}

        return await run_blocking(_update)

    @exposed(timeout=30)
    async def delete_document(self, conn_id: str, collection: str, doc_id: str) -> DocumentOpResult:
        def _delete():
            try:
                client = self._mgr.get_client(conn_id)
                col = client.get_collection(name=collection)
                col.delete(ids=[doc_id])
                logger.info("Document deleted: conn={} collection={} id={}", conn_id, collection, doc_id)
                return {"success": True}
            except Exception as e:
                logger.error("delete_document failed: conn={} collection={} id={} error={}", conn_id, collection, doc_id, e)
                return {"success": False, "error": str(e)}

        return await run_blocking(_delete)

    @exposed(timeout=300)
    async def seed_test_data(self, conn_id: str, collection: str) -> SeedResult:
        def _seed():
            try:
                client = self._mgr.get_client(conn_id)
                col = client.get_collection(name=collection)
                ids, documents, metadatas, embeddings = [], [], [], []
                for text, category, idx in _SEED_DOCS:
                    doc_id = f"seed-{uuid.uuid4().hex[:8]}"
                    emb = call_embedding(conn_id, collection, text)
                    ids.append(doc_id)
                    documents.append(text)
                    metadatas.append({"category": category, "index": idx})
                    if emb:
                        embeddings.append(emb)
                kwargs: dict = {"ids": ids, "documents": documents, "metadatas": metadatas}
                if len(embeddings) == len(ids):
                    kwargs["embeddings"] = embeddings
                col.add(**kwargs)
                logger.info("Seed data added: conn={} collection={} count={}", conn_id, collection, len(ids))
                return {"success": True, "count": len(ids)}
            except Exception as e:
                logger.error("seed_test_data failed: conn={} collection={} error={}", conn_id, collection, e)
                return {"success": False, "error": str(e)}

        return await run_blocking(_seed)
