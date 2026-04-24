import type { Connection, Collection, Document, QueryResultItem, EmbeddingConfig } from '../types'

declare global {
  interface Window {
    pywebview?: { api: PythonAPI }
  }
}

interface PythonAPI {
  get_connections(): Promise<Connection[]>
  add_connection(name: string, conn_type: string, host: string, port: number, is_local: boolean, path: string, token: string): Promise<Connection>
  update_connection(conn_id: string, name: string, conn_type: string, host: string, port: number, is_local: boolean, path: string, token: string): Promise<Connection>
  remove_connection(conn_id: string): Promise<boolean>
  test_connection(conn_type: string, host: string, port: number, path: string, token: string): Promise<{ success: boolean; error?: string }>
  connect(conn_id: string): Promise<{ success: boolean; error?: string }>
  disconnect(conn_id: string): Promise<boolean>
  pick_directory(): Promise<string | null>

  list_collections(conn_id: string): Promise<Collection[]>
  create_collection(conn_id: string, name: string, metadata_json?: string): Promise<{ success: boolean; name?: string; error?: string }>
  modify_collection(conn_id: string, old_name: string, new_name: string, metadata_json?: string): Promise<{ success: boolean; name?: string; error?: string }>
  delete_collection(conn_id: string, name: string): Promise<{ success: boolean; error?: string }>
  get_collection_info(conn_id: string, name: string): Promise<Collection>
  seed_test_data(conn_id: string, collection: string): Promise<{ success: boolean; count?: number; error?: string }>

  get_collection_embedding(conn_id: string, collection: string): Promise<EmbeddingConfig>
  set_collection_embedding(conn_id: string, collection: string, embedding_url: string, embedding_model: string, embedding_api_key: string, dimension?: number): Promise<{ success: boolean }>
  clear_collection_embedding(conn_id: string, collection: string): Promise<{ success: boolean }>
  test_embedding(conn_id: string, collection: string, text: string): Promise<{ dimension?: number; preview?: number[]; error?: string }>

  get_documents(conn_id: string, collection: string, limit: number, offset: number, include_embeddings?: boolean): Promise<{ total: number; items: Document[]; error?: string }>
  add_document(conn_id: string, collection: string, doc_id: string, document: string, metadata_json: string): Promise<{ success: boolean; error?: string }>
  update_document(conn_id: string, collection: string, doc_id: string, document: string, metadata_json: string): Promise<{ success: boolean; error?: string }>
  delete_document(conn_id: string, collection: string, doc_id: string): Promise<{ success: boolean; error?: string }>

  get_embedding_info(conn_id: string, collection: string): Promise<{ dimension: number | null; error?: string }>
  query(conn_id: string, collection: string, query_text: string, n_results: number, where_json: string): Promise<{ items: QueryResultItem[]; error?: string }>
}

function waitForApi(): Promise<PythonAPI> {
  return new Promise((resolve) => {
    const check = () => window.pywebview?.api ? resolve(window.pywebview.api) : setTimeout(check, 100)
    check()
  })
}

let _api: PythonAPI | null = null
async function getApi(): Promise<PythonAPI> {
  if (!_api) _api = await waitForApi()
  return _api
}

export const bridge = {
  getConnections: () => getApi().then(a => a.get_connections()),
  addConnection: (name: string, conn_type: string, host: string, port: number, is_local: boolean, path: string, token: string) =>
    getApi().then(a => a.add_connection(name, conn_type, host, port, is_local, path, token)),
  updateConnection: (conn_id: string, name: string, conn_type: string, host: string, port: number, is_local: boolean, path: string, token: string) =>
    getApi().then(a => a.update_connection(conn_id, name, conn_type, host, port, is_local, path, token)),
  removeConnection: (conn_id: string) => getApi().then(a => a.remove_connection(conn_id)),
  testConnection: (conn_type: string, host: string, port: number, path: string, token: string) =>
    getApi().then(a => a.test_connection(conn_type, host, port, path, token)),
  connect: (conn_id: string) => getApi().then(a => a.connect(conn_id)),
  disconnect: (conn_id: string) => getApi().then(a => a.disconnect(conn_id)),
  pickDirectory: () => getApi().then(a => a.pick_directory()),

  listCollections: (conn_id: string) => getApi().then(a => a.list_collections(conn_id)),
  createCollection: (conn_id: string, name: string, metadata_json = '') => getApi().then(a => a.create_collection(conn_id, name, metadata_json)),
  modifyCollection: (conn_id: string, old_name: string, new_name: string, metadata_json = '') => getApi().then(a => a.modify_collection(conn_id, old_name, new_name, metadata_json)),
  deleteCollection: (conn_id: string, name: string) => getApi().then(a => a.delete_collection(conn_id, name)),
  getCollectionInfo: (conn_id: string, name: string) => getApi().then(a => a.get_collection_info(conn_id, name)),

  getCollectionEmbedding: (conn_id: string, collection: string) =>
    getApi().then(a => a.get_collection_embedding(conn_id, collection)),
  setCollectionEmbedding: (conn_id: string, collection: string, url: string, model: string, apiKey: string, dimension?: number) =>
    getApi().then(a => a.set_collection_embedding(conn_id, collection, url, model, apiKey, dimension ?? 0)),
  clearCollectionEmbedding: (conn_id: string, collection: string) =>
    getApi().then(a => a.clear_collection_embedding(conn_id, collection)),
  testEmbedding: (conn_id: string, collection: string, text: string) =>
    getApi().then(a => a.test_embedding(conn_id, collection, text)),

  seedTestData: (conn_id: string, collection: string) =>
    getApi().then(a => a.seed_test_data(conn_id, collection)),
  getDocuments: (conn_id: string, collection: string, limit: number, offset: number, includeEmbeddings?: boolean) =>
    getApi().then(a => a.get_documents(conn_id, collection, limit, offset, includeEmbeddings ?? false)),
  addDocument: (conn_id: string, collection: string, doc_id: string, document: string, metadata_json: string) =>
    getApi().then(a => a.add_document(conn_id, collection, doc_id, document, metadata_json)),
  updateDocument: (conn_id: string, collection: string, doc_id: string, document: string, metadata_json: string) =>
    getApi().then(a => a.update_document(conn_id, collection, doc_id, document, metadata_json)),
  deleteDocument: (conn_id: string, collection: string, doc_id: string) =>
    getApi().then(a => a.delete_document(conn_id, collection, doc_id)),

  getEmbeddingInfo: (conn_id: string, collection: string) =>
    getApi().then(a => a.get_embedding_info(conn_id, collection)),
  query: (conn_id: string, collection: string, query_text: string, n_results: number, where_json: string) =>
    getApi().then(a => a.query(conn_id, collection, query_text, n_results, where_json)),
}
