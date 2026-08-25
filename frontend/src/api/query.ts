// 此文件由 gen.py 自动生成，请勿手动修改。
// 源定义：backend/features/query/bridge.py

import { getProxy } from "@/bridge";

export interface QueryResultItem {
  id: string;
  document: string;
  metadata: Record<string, object>;
  distance: number | null;
}

export interface QueryResult {
  items?: QueryResultItem[];
  error?: string;
}

const _proxy = getProxy("query");

export const queryApi = {
  query: async (conn_id: string, collection: string, query_text: string, n_results: number, where_json: string) =>
    await _proxy.invoke<QueryResult>("query", { conn_id, collection, query_text, n_results, where_json }),
};
