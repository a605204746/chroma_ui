// 此文件由 gen.py 自动生成，请勿手动修改。
// 源定义：backend/features/connection/bridge.py

import { getProxy } from "@/bridge";

export interface Connection {
  id: string;
  name: string;
  conn_type: "http" | "persistent";
  host: string;
  port: number;
  is_local: boolean;
  path: string;
  token: string;
  connected: boolean;
}

export interface ConnectionOpResult {
  success: boolean;
  error?: string;
}

const _proxy = getProxy("connection");

export const connectionApi = {
  getConnections: async () =>
    await _proxy.invoke<Connection[]>("get_connections"),
  addConnection: async (name: string, conn_type: string, host: string, port: number, is_local: boolean, path: string, token: string = "") =>
    await _proxy.invoke<Connection>("add_connection", { name, conn_type, host, port, is_local, path, token }),
  updateConnection: async (conn_id: string, name: string, conn_type: string, host: string, port: number, is_local: boolean, path: string, token: string = "") =>
    await _proxy.invoke<Connection>("update_connection", { conn_id, name, conn_type, host, port, is_local, path, token }),
  removeConnection: async (conn_id: string) =>
    await _proxy.invoke<boolean>("remove_connection", { conn_id }),
  testConnection: async (conn_type: string, host: string, port: number, path: string, token: string = "") =>
    await _proxy.invoke<ConnectionOpResult>("test_connection", { conn_type, host, port, path, token }),
  connect: async (conn_id: string) =>
    await _proxy.invoke<ConnectionOpResult>("connect", { conn_id }),
  disconnect: async (conn_id: string) =>
    await _proxy.invoke<boolean>("disconnect", { conn_id }),
  pickDirectory: async () =>
    await _proxy.invoke<string | null>("pick_directory"),
};
