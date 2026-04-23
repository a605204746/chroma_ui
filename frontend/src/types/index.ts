export interface Connection {
  id: string
  name: string
  conn_type: 'http' | 'persistent'
  host: string
  port: number
  is_local: boolean
  path: string
  token: string
  connected: boolean
}

export interface EmbeddingConfig {
  embedding_url: string
  embedding_model: string
  embedding_api_key: string
  dimension?: number
}

export interface Collection {
  name: string
  count: number
  metadata: Record<string, unknown>
  has_embedding: boolean
}

export interface Document {
  id: string
  document: string
  metadata: Record<string, unknown>
  embedding?: number[] | null
}

export interface QueryResultItem {
  id: string
  document: string
  metadata: Record<string, unknown>
  distance: number | null
}

export interface ApiResponse<T = unknown> {
  error?: string
  success?: boolean
  data?: T
}
