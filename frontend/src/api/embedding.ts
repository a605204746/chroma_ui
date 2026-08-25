// 此文件由 gen.py 自动生成，请勿手动修改。
// 源定义：backend/features/embedding/bridge.py

import { getProxy } from "@/bridge";

export interface EmbeddingConfig {
  embedding_url: string;
  embedding_model: string;
  embedding_api_key: string;
  dimension?: number;
}

export interface EmbeddingOpResult {
  success: boolean;
}

export interface TestEmbeddingResult {
  dimension?: number;
  preview?: number[];
  error?: string;
}

export interface EmbeddingInfo {
  dimension?: number | null;
  error?: string;
}

const _proxy = getProxy("embedding");

export const embeddingApi = {
  getCollectionEmbedding: async (conn_id: string, collection: string) =>
    await _proxy.invoke<EmbeddingConfig>("get_collection_embedding", { conn_id, collection }),
  setCollectionEmbedding: async (conn_id: string, collection: string, embedding_url: string, embedding_model: string, embedding_api_key: string, dimension: number = 0) =>
    await _proxy.invoke<EmbeddingOpResult>("set_collection_embedding", { conn_id, collection, embedding_url, embedding_model, embedding_api_key, dimension }),
  clearCollectionEmbedding: async (conn_id: string, collection: string) =>
    await _proxy.invoke<EmbeddingOpResult>("clear_collection_embedding", { conn_id, collection }),
  testEmbedding: async (conn_id: string, collection: string, text: string) =>
    await _proxy.invoke<TestEmbeddingResult>("test_embedding", { conn_id, collection, text }),
  getEmbeddingInfo: async (conn_id: string, collection: string) =>
    await _proxy.invoke<EmbeddingInfo>("get_embedding_info", { conn_id, collection }),
};
