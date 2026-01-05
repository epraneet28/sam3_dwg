/**
 * useDocumentSync - Synchronizes frontend document store with backend storage
 *
 * This hook runs on app initialization to:
 * 1. Fetch the document list from the backend
 * 2. Remove any frontend documents that no longer exist on the backend
 * 3. Mark documents with empty pages for re-segmentation
 *
 * This prevents 404 errors from stale localStorage data.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useStore, useDocuments, useHasHydrated } from '../store';
import { api } from '../api/client';
import type { DocumentMetadata } from '../types';

interface SyncResult {
  synced: boolean;
  removedCount: number;
  removedDocuments: string[];
  error: string | null;
}

interface UseDocumentSyncOptions {
  /** Enable automatic sync on mount (default: true) */
  autoSync?: boolean;
  /** Show console logs for debugging (default: false) */
  debug?: boolean;
  /** Callback when documents are removed */
  onDocumentsRemoved?: (removed: string[]) => void;
  /** Callback on sync error */
  onError?: (error: string) => void;
}

export function useDocumentSync(options: UseDocumentSyncOptions = {}) {
  const { autoSync = true, debug = false, onDocumentsRemoved, onError } = options;

  const documents = useDocuments();
  const hasHydrated = useHasHydrated();
  const { deleteDocument, updateDocument } = useStore();

  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSyncResult, setLastSyncResult] = useState<SyncResult | null>(null);
  const hasSyncedRef = useRef(false);

  const log = useCallback((message: string, ...args: unknown[]) => {
    if (debug) {
      console.log(`[DocumentSync] ${message}`, ...args);
    }
  }, [debug]);

  /**
   * Synchronize frontend documents with backend storage
   */
  const syncDocuments = useCallback(async (): Promise<SyncResult> => {
    if (isSyncing) {
      return { synced: false, removedCount: 0, removedDocuments: [], error: 'Sync already in progress' };
    }

    setIsSyncing(true);
    log('Starting document sync...');

    try {
      // Fetch documents from backend
      let backendDocuments: DocumentMetadata[];
      try {
        backendDocuments = await api.listDocuments();
        log(`Backend has ${backendDocuments.length} documents`);
      } catch (fetchError) {
        // If backend is unavailable, don't remove anything
        const errorMsg = fetchError instanceof Error ? fetchError.message : 'Failed to fetch documents';
        log('Backend unavailable, skipping sync:', errorMsg);
        const result: SyncResult = { synced: false, removedCount: 0, removedDocuments: [], error: errorMsg };
        setLastSyncResult(result);
        onError?.(errorMsg);
        return result;
      }

      // Create a set of backend document IDs for fast lookup
      const backendDocIds = new Set(backendDocuments.map(d => d.doc_id));
      log('Backend document IDs:', Array.from(backendDocIds));

      // Find frontend documents that don't exist on backend
      const staleDocuments: string[] = [];
      const documentsNeedingResegment: string[] = [];

      for (const frontendDoc of documents) {
        if (!backendDocIds.has(frontendDoc.id)) {
          // Document doesn't exist on backend - mark for removal
          staleDocuments.push(frontendDoc.id);
          log(`Stale document found: ${frontendDoc.id} (${frontendDoc.name})`);
        } else if (!frontendDoc.pages || frontendDoc.pages.length === 0) {
          // Document exists but has no pages - needs re-segmentation
          documentsNeedingResegment.push(frontendDoc.id);
          log(`Document needs re-segmentation: ${frontendDoc.id} (${frontendDoc.name})`);
        }
      }

      // Remove stale documents from frontend store
      for (const docId of staleDocuments) {
        log(`Removing stale document: ${docId}`);
        deleteDocument(docId);
      }

      // Mark documents needing re-segmentation with error status
      for (const docId of documentsNeedingResegment) {
        log(`Marking document for re-segmentation: ${docId}`);
        updateDocument(docId, {
          status: 'error',
          error: 'Pages missing - please re-upload or delete this document',
        });
      }

      const result: SyncResult = {
        synced: true,
        removedCount: staleDocuments.length,
        removedDocuments: staleDocuments,
        error: null,
      };

      setLastSyncResult(result);

      if (staleDocuments.length > 0) {
        log(`Removed ${staleDocuments.length} stale documents`);
        onDocumentsRemoved?.(staleDocuments);
      }

      log('Sync complete');
      return result;

    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown sync error';
      log('Sync error:', errorMsg);
      const result: SyncResult = { synced: false, removedCount: 0, removedDocuments: [], error: errorMsg };
      setLastSyncResult(result);
      onError?.(errorMsg);
      return result;
    } finally {
      setIsSyncing(false);
    }
  }, [isSyncing, documents, deleteDocument, updateDocument, log, onDocumentsRemoved, onError]);

  // Auto-sync on mount (only once, after hydration)
  useEffect(() => {
    // Wait for store to hydrate from localStorage before syncing
    if (!hasHydrated) {
      return;
    }

    if (autoSync && !hasSyncedRef.current) {
      hasSyncedRef.current = true;
      log('Store hydrated, starting sync...');
      syncDocuments();
    }
  }, [autoSync, hasHydrated, syncDocuments, log]);

  return {
    /** Whether sync is currently in progress */
    isSyncing,
    /** Result of the last sync operation */
    lastSyncResult,
    /** Manually trigger a sync */
    syncDocuments,
  };
}

/**
 * Hook variant that provides a simple notification when stale documents are removed
 */
export function useDocumentSyncWithNotification() {
  const [notification, setNotification] = useState<string | null>(null);

  const { isSyncing, lastSyncResult, syncDocuments } = useDocumentSync({
    autoSync: true,
    debug: import.meta.env.DEV,
    onDocumentsRemoved: (removed) => {
      if (removed.length === 1) {
        setNotification('1 outdated document reference was cleaned up');
      } else if (removed.length > 1) {
        setNotification(`${removed.length} outdated document references were cleaned up`);
      }
      // Auto-dismiss after 5 seconds
      setTimeout(() => setNotification(null), 5000);
    },
    onError: (error) => {
      // Only show error if it's not just "backend unavailable"
      if (!error.includes('ECONNREFUSED') && !error.includes('Network Error')) {
        console.warn('[DocumentSync] Error:', error);
      }
    },
  });

  const dismissNotification = useCallback(() => {
    setNotification(null);
  }, []);

  return {
    isSyncing,
    lastSyncResult,
    syncDocuments,
    notification,
    dismissNotification,
  };
}

export default useDocumentSync;
