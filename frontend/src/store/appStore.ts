import { create } from 'zustand'
import type { Connection, Collection } from '../types'

export type NavPage = 'overview' | 'collections' | 'collection-detail'
export type ThemeMode = 'light' | 'dark' | 'system'

function resolveIsDark(mode: ThemeMode): boolean {
  if (mode === 'dark') return true
  if (mode === 'light') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

interface AppState {
  connections: Connection[]
  activeConnId: string | null
  activeCollection: string | null
  collections: Collection[]
  currentNav: NavPage
  themeMode: ThemeMode
  isDark: boolean

  setConnections: (connections: Connection[]) => void
  setActiveConnId: (id: string | null) => void
  setActiveCollection: (name: string | null) => void
  setCollections: (collections: Collection[]) => void
  setCurrentNav: (nav: NavPage) => void
  updateConnectionStatus: (id: string, connected: boolean) => void
  navigateToCollection: (name: string) => void
  backToCollections: () => void
  setThemeMode: (mode: ThemeMode) => void
  syncSystemTheme: () => void
  toggleDark: () => void
}

const savedMode = (localStorage.getItem('chroma-ui-theme') as ThemeMode | null) ?? 'system'

export const useAppStore = create<AppState>((set, get) => ({
  connections: [],
  activeConnId: null,
  activeCollection: null,
  collections: [],
  currentNav: 'overview',
  themeMode: savedMode,
  isDark: resolveIsDark(savedMode),

  setConnections: (connections) => set({ connections }),
  setActiveConnId: (activeConnId) =>
    set({ activeConnId, activeCollection: null, currentNav: 'overview' }),
  setActiveCollection: (activeCollection) => set({ activeCollection }),
  setCollections: (collections) => set({ collections }),
  setCurrentNav: (currentNav) => set({ currentNav }),
  updateConnectionStatus: (id, connected) =>
    set((state) => ({
      connections: state.connections.map((c) => (c.id === id ? { ...c, connected } : c)),
    })),
  navigateToCollection: (name) =>
    set({ activeCollection: name, currentNav: 'collection-detail' }),
  backToCollections: () =>
    set({ activeCollection: null, currentNav: 'collections' }),
  setThemeMode: (mode) => {
    localStorage.setItem('chroma-ui-theme', mode)
    set({ themeMode: mode, isDark: resolveIsDark(mode) })
  },
  syncSystemTheme: () => {
    const { themeMode } = get()
    if (themeMode === 'system') {
      set({ isDark: resolveIsDark('system') })
    }
  },
  toggleDark: () => {
    const next = !get().isDark
    const mode: ThemeMode = next ? 'dark' : 'light'
    localStorage.setItem('chroma-ui-theme', mode)
    set({ themeMode: mode, isDark: next })
  },
}))
