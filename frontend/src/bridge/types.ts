/** 事件监听器类型 */
export type EventListener<T = unknown> = (payload: T) => void;

/** 桥接器代理对象 */
export interface BridgeProxy {
  invoke<T = unknown>(
    method: string,
    payload?: Record<string, unknown>
  ): Promise<T>;
  on<T = unknown>(eventName: string, listener: EventListener<T>): () => void;
  off<T = unknown>(eventName: string, listener: EventListener<T>): void;
}
