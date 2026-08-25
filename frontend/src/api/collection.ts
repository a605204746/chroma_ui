// 此文件由 gen.py 自动生成，请勿手动修改。
// 源定义：backend/features/collection/bridge.py

import { getProxy } from "@/bridge";

export interface Collection {
  name: string;
  count: number;
  metadata: Record<string, object>;
  has_embedding: boolean;
}

export interface CollectionMutationResult {
  success?: boolean;
  name?: string;
  error?: string;
}

export interface CollectionOpResult {
  success?: boolean;
  error?: string;
}

export interface CollectionDetail {
  name?: string;
  count?: number;
  metadata?: Record<string, object>;
  error?: string;
}

const _proxy = getProxy("collection");

export const collectionApi = {
  listCollections: async (conn_id: string) =>
    await _proxy.invoke<Collection[]>("list_collections", { conn_id }),
  createCollection: async (conn_id: string, name: string, metadata_json: string = "") =>
    await _proxy.invoke<CollectionMutationResult>("create_collection", { conn_id, name, metadata_json }),
  modifyCollection: async (conn_id: string, old_name: string, new_name: string, metadata_json: string = "") =>
    await _proxy.invoke<CollectionMutationResult>("modify_collection", { conn_id, old_name, new_name, metadata_json }),
  deleteCollection: async (conn_id: string, name: string) =>
    await _proxy.invoke<CollectionOpResult>("delete_collection", { conn_id, name }),
  getCollectionInfo: async (conn_id: string, name: string) =>
    await _proxy.invoke<CollectionDetail>("get_collection_info", { conn_id, name }),
};
