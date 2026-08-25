import type { BridgeProxy, EventListener } from "@/bridge/types";

type DispatchResult = { ok: boolean; data?: unknown; error?: string; traceback?: string };
type EventReducer = (items: unknown[]) => unknown;
type BufferedEvent = { items: unknown[]; reducer?: EventReducer };

declare global {
  interface Window {
    pywebview: {
      api: {
        dispatch: (
          bridge: string,
          method: string,
          payload?: Record<string, unknown> | unknown[]
        ) => Promise<DispatchResult>;
      };
    };
    // Python 批量推送的接收函数，由本模块在加载时设置
    __pyBatch: (items: Array<[string, string, unknown]>) => void;
  }
}

// ─── 内部状态 ──────────────────────────────────────────────────────────────

let _ready = false;
let _initError: Error | null = null;
const _proxyCache = new Map<string, BridgeProxy>();
const _pendingReady: Array<{ resolve: () => void; reject: (e: Error) => void }> = [];

// bridge_name → event_name → listeners
const _eventListeners = new Map<string, Map<string, Set<EventListener>>>();
const _bufferedEvents = new Map<string, BufferedEvent>();
let _flushScheduled = false;

// 事件 reducer 注册表：key 为 "bridge.eventName"，可用 registerEventReducer 追加
const _eventReducers = new Map<string, EventReducer>();

// ─── Python 批量推送接收 ────────────────────────────────────────────────────

// 在模块加载时立即设置，确保 Python 端 on_loaded 触发前已就绪
window.__pyBatch = (items) => {
  for (const [bridge, event, data] of items) {
    const key = `${bridge}.${event}`;
    const buffered = _bufferedEvents.get(key);

    if (buffered) {
      buffered.items.push(data);
    } else {
      _bufferedEvents.set(key, {
        items: [data],
        reducer: _eventReducers.get(key),
      });
    }
  }

  _scheduleEventFlush();
};

function _scheduleEventFlush() {
  if (_flushScheduled) return;
  _flushScheduled = true;

  const scheduler = window.requestAnimationFrame
    ? window.requestAnimationFrame.bind(window)
    : (cb: FrameRequestCallback) => window.setTimeout(cb, 16);

  scheduler(() => {
    _flushScheduled = false;

    for (const [key, buffered] of _bufferedEvents) {
      _bufferedEvents.delete(key);

      const dot = key.indexOf(".");
      const bridge = key.slice(0, dot);
      const event = key.slice(dot + 1);
      const listeners = _eventListeners.get(bridge)?.get(event);
      if (!listeners?.size) continue;

      if (buffered.reducer) {
        listeners.forEach((fn) => fn(buffered.reducer!(buffered.items)));
      } else {
        for (const item of buffered.items) {
          listeners.forEach((fn) => fn(item));
        }
      }
    }
  });
}

// ─── 初始化 ────────────────────────────────────────────────────────────────

/**
 * 初始化 pywebview 桥接。在 main.tsx 中调用一次。
 * 等待 pywebview 注入 window.pywebview.api 后标记为就绪。
 * 在纯浏览器环境中调用时会超时抛出异常，main.tsx 负责 catch 降级。
 */
export async function initBridge(): Promise<void> {
  try {
    await _waitForPywebview();
    _ready = true;
    _pendingReady.splice(0).forEach(({ resolve }) => resolve());
  } catch (e) {
    _initError = e instanceof Error ? e : new Error(String(e));
    _pendingReady.splice(0).forEach(({ reject }) => reject(_initError!));
    throw e;
  }
}

function _waitForPywebview(totalMs = 10_000): Promise<void> {
  // pywebview 注入完成后 dispatch "pywebviewready" 事件（finish.js），直接监听，无需轮询
  if (window.pywebview?.api) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      window.removeEventListener("pywebviewready", onReady);
      reject(new Error("pywebview API not available. Make sure the app is running inside pywebview."));
    }, totalMs);
    function onReady() {
      clearTimeout(timer);
      resolve();
    }
    window.addEventListener("pywebviewready", onReady, { once: true });
  });
}

function _ensureReady(): Promise<void> {
  if (_ready) return Promise.resolve();
  if (_initError) return Promise.reject(_initError);
  return new Promise((resolve, reject) => _pendingReady.push({ resolve, reject }));
}

// ─── 公开 API ──────────────────────────────────────────────────────────────

/**
 * 注册事件 reducer。key 格式为 "bridge.eventName"。
 * reducer 接收同帧内所有 payload 数组，返回最终派发给监听器的值。
 * 适用于需要将多条消息合并为一次调用的流式事件。
 */
export function registerEventReducer(key: string, reducer: EventReducer): void {
  _eventReducers.set(key, reducer);
}

/**
 * 获取指定桥接器的代理对象。
 *
 * const connection = getProxy("connection");
 * const conns = await connection.invoke("get_connections");
 */
export function getProxy(bridgeName: string): BridgeProxy {
  const cached = _proxyCache.get(bridgeName);
  if (cached) return cached;

  const proxy: BridgeProxy = {
    async invoke<T>(
      method: string,
      payload: Record<string, unknown> = {}
    ): Promise<T> {
      await _ensureReady();

      const result = await window.pywebview.api.dispatch(bridgeName, method, payload);

      if (!result.ok) {
        throw new Error(result.error ?? "Unknown error");
      }
      return result.data as T;
    },

    on<T>(eventName: string, listener: EventListener<T>): () => void {
      if (!_eventListeners.has(bridgeName)) {
        _eventListeners.set(bridgeName, new Map());
      }
      const bridge = _eventListeners.get(bridgeName)!;
      if (!bridge.has(eventName)) {
        bridge.set(eventName, new Set());
      }
      bridge.get(eventName)!.add(listener as EventListener);
      return () => proxy.off(eventName, listener);
    },

    off<T>(eventName: string, listener: EventListener<T>): void {
      _eventListeners.get(bridgeName)?.get(eventName)?.delete(listener as EventListener);
    },
  };

  _proxyCache.set(bridgeName, proxy);
  return proxy;
}
