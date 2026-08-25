import {useCallback, useEffect, useRef, useState} from "react";
import {getProxy} from "@/bridge/channel";
import type {BridgeProxy, EventListener} from "@/bridge/types";

/**
 * 调用 Python 方法的 hook。
 *
 * const { data, loading, error, execute } = useInvoke<Connection[]>("connection", "get_connections");
 * useEffect(() => { execute(); }, [execute]);
 */
export function useInvoke<T>(
  bridgeName: string,
  method: string,
  defaultPayload?: Record<string, unknown>
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const reqId = useRef(0);
  const defaultPayloadRef = useRef(defaultPayload);
  useEffect(() => {
    defaultPayloadRef.current = defaultPayload;
  });

  const execute = useCallback(
    async (runtimePayload?: Record<string, unknown>): Promise<T | null> => {
      const id = ++reqId.current;
      setLoading(true);
      setError(null);
      try {
        const result = await getProxy(bridgeName).invoke<T>(
          method,
          runtimePayload ?? defaultPayloadRef.current ?? {}
        );
        if (id === reqId.current) {
          setData(result);
        }
        return result;
      } catch (e) {
        const err = e instanceof Error ? e : new Error(String(e));
        if (id === reqId.current) {
          setError(err);
        }
        return null;
      } finally {
        if (id === reqId.current) {
          setLoading(false);
        }
      }
    },
    [bridgeName, method]
  );

  return { data, loading, error, execute };
}

/**
 * 订阅 Python 主动推送事件的 hook，组件卸载时自动取消订阅。
 *
 * useEvent("system", "themeChanged", ({ theme }) => setTheme(theme));
 */
export function useEvent<T>(
  bridgeName: string,
  eventName: string,
  listener: EventListener<T>
) {
  const listenerRef = useRef(listener);
  useEffect(() => {
    listenerRef.current = listener;
  });

  useEffect(() => {
    const stable: EventListener<T> = (payload) => listenerRef.current(payload);
    return getProxy(bridgeName).on(eventName, stable);
  }, [bridgeName, eventName]);
}

/**
 * 获取 Bridge Proxy 的 hook，用于命令式调用。
 *
 * const connection = useBridge("connection");
 * await connection.invoke("connect", { conn_id: "..." });
 */
export function useBridge(bridgeName: string): BridgeProxy {
  return getProxy(bridgeName);
}
