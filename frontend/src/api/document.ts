// 此文件由 gen.py 自动生成，请勿手动修改。
// 源定义：backend/features/document/bridge.py

import { getProxy } from "@/bridge";

export interface DocumentWithEmbedding {
  id: string;
  document: string;
  metadata: Record<string, object>;
  embedding?: number[] | null;
}

export interface DocumentsResult {
  total?: number;
  items?: DocumentWithEmbedding[];
  error?: string;
}

export interface DocumentOpResult {
  success?: boolean;
  error?: string;
}

export interface SeedResult {
  success?: boolean;
  count?: number;
  error?: string;
}

const _proxy = getProxy("document");

export const documentApi = {
  getDocuments: async (conn_id: string, collection: string, limit: number = 20, offset: number = 0, include_embeddings: boolean = false) =>
    await _proxy.invoke<DocumentsResult>("get_documents", { conn_id, collection, limit, offset, include_embeddings }),
  addDocument: async (conn_id: string, collection: string, doc_id: string, document: string, metadata_json: string) =>
    await _proxy.invoke<DocumentOpResult>("add_document", { conn_id, collection, doc_id, document, metadata_json }),
  updateDocument: async (conn_id: string, collection: string, doc_id: string, document: string, metadata_json: string) =>
    await _proxy.invoke<DocumentOpResult>("update_document", { conn_id, collection, doc_id, document, metadata_json }),
  deleteDocument: async (conn_id: string, collection: string, doc_id: string) =>
    await _proxy.invoke<DocumentOpResult>("delete_document", { conn_id, collection, doc_id }),
  seedTestData: async (conn_id: string, collection: string) =>
    await _proxy.invoke<SeedResult>("seed_test_data", { conn_id, collection }),
};
