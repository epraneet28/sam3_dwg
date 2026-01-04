import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { SAM3Document, ZonePromptConfig, InferenceSettings } from '../types';

interface AppState {
  // Documents
  documents: SAM3Document[];
  selectedDocument: SAM3Document | null;

  // Prompt Configuration
  promptConfig: ZonePromptConfig[];
  inferenceSettings: InferenceSettings;
  configVersion: number;
  configLoaded: boolean;

  // Dashboard UI state
  dashboardSearch: string;

  // Sidebar UI state
  sidebarCollapsed: boolean;

  // Document Actions
  setDocuments: (documents: SAM3Document[]) => void;
  addDocument: (document: SAM3Document) => void;
  updateDocument: (id: string, updates: Partial<SAM3Document>) => void;
  selectDocument: (document: SAM3Document | null) => void;
  deleteDocument: (id: string) => void;

  // Config Actions
  setPromptConfig: (prompts: ZonePromptConfig[], inference: InferenceSettings, version: number) => void;
  updatePrompt: (zoneType: string, updates: Partial<ZonePromptConfig>) => void;
  togglePromptEnabled: (zoneType: string) => void;
  setInferenceSettings: (settings: Partial<InferenceSettings>) => void;
  incrementConfigVersion: () => void;

  // UI Actions
  setDashboardSearch: (search: string) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // Initial state - Documents
      documents: [],
      selectedDocument: null,

      // Initial state - Config
      promptConfig: [],
      inferenceSettings: { confidence_threshold: 0.3, return_masks: true },
      configVersion: 0,
      configLoaded: false,

      // Initial state - UI
      dashboardSearch: '',
      sidebarCollapsed: false,

      // Document Actions
      setDocuments: (documents) => set({ documents }),

      addDocument: (document) =>
        set((state) => ({
          documents: [document, ...state.documents],
        })),

      updateDocument: (id, updates) =>
        set((state) => ({
          documents: state.documents.map((doc) =>
            doc.id === id ? { ...doc, ...updates } : doc
          ),
          selectedDocument:
            state.selectedDocument?.id === id
              ? { ...state.selectedDocument, ...updates }
              : state.selectedDocument,
        })),

      selectDocument: (document) => set({ selectedDocument: document }),

      deleteDocument: (id) =>
        set((state) => ({
          documents: state.documents.filter((doc) => doc.id !== id),
          selectedDocument:
            state.selectedDocument?.id === id ? null : state.selectedDocument,
        })),

      // Config Actions
      setPromptConfig: (prompts, inference, version) =>
        set({
          promptConfig: prompts,
          inferenceSettings: inference,
          configVersion: version,
          configLoaded: true,
        }),

      updatePrompt: (zoneType, updates) =>
        set((state) => ({
          promptConfig: state.promptConfig.map((p) =>
            p.zone_type === zoneType ? { ...p, ...updates } : p
          ),
        })),

      togglePromptEnabled: (zoneType) =>
        set((state) => ({
          promptConfig: state.promptConfig.map((p) =>
            p.zone_type === zoneType ? { ...p, enabled: !p.enabled } : p
          ),
        })),

      setInferenceSettings: (settings) =>
        set((state) => ({
          inferenceSettings: { ...state.inferenceSettings, ...settings },
        })),

      incrementConfigVersion: () =>
        set((state) => ({
          configVersion: state.configVersion + 1,
        })),

      // UI Actions
      setDashboardSearch: (search) => set({ dashboardSearch: search }),

      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
    }),
    {
      name: 'sam3-storage',
      partialize: (state) => ({
        documents: state.documents,
        // Persist config for offline access
        promptConfig: state.promptConfig,
        inferenceSettings: state.inferenceSettings,
        configVersion: state.configVersion,
        configLoaded: state.configLoaded,
      }),
    }
  )
);

// Document Selectors
export const useDocuments = () => useStore((state) => state.documents);
export const useSelectedDocument = () => useStore((state) => state.selectedDocument);

// Config Selectors
export const usePromptConfig = () => useStore((state) => state.promptConfig);
export const useInferenceSettings = () => useStore((state) => state.inferenceSettings);
export const useConfigVersion = () => useStore((state) => state.configVersion);
export const useConfigLoaded = () => useStore((state) => state.configLoaded);
export const useEnabledPrompts = () =>
  useStore((state) => state.promptConfig.filter((p) => p.enabled));

// UI Selectors
export const useDashboardSearch = () => useStore((state) => state.dashboardSearch);
export const useSidebarCollapsed = () => useStore((state) => state.sidebarCollapsed);
