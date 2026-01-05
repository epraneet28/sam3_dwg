import { Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { Layout } from './components/layout';
import Dashboard from './pages/Dashboard';
import Viewer from './pages/Viewer';
import Settings from './pages/Settings';
import Playground from './pages/Playground';
import { api } from './api/client';
import { useDocumentSyncWithNotification } from './hooks/useDocumentSync';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 1,
    },
  },
});

function AppContent() {
  // Health check on mount
  const { data: health, isError } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30000, // Check every 30s
    retry: false,
  });

  // Sync documents with backend on mount
  // This removes stale document references that no longer exist on the backend
  const { notification, dismissNotification } = useDocumentSyncWithNotification();

  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="viewer/:docId" element={<Viewer />} />
          <Route path="settings" element={<Settings />} />
          <Route path="playground" element={<Playground />} />
        </Route>
      </Routes>

      {/* Document sync notification */}
      {notification && (
        <div className="fixed bottom-4 right-4 z-50 flex items-center gap-3 px-4 py-3 bg-blue-500/10 border border-blue-500/50 rounded-lg text-blue-400 text-sm shadow-lg">
          <span>{notification}</span>
          <button
            onClick={dismissNotification}
            className="text-blue-400 hover:text-blue-300 font-bold"
            aria-label="Dismiss"
          >
            &times;
          </button>
        </div>
      )}

      {/* Health status badges */}
      {isError && (
        <div className="fixed bottom-4 left-20 z-50 px-3 py-2 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-xs">
          Backend offline (using mock mode)
        </div>
      )}
      {health && !health.model_loaded && (
        <div className="fixed bottom-4 left-20 z-50 px-3 py-2 bg-yellow-500/10 border border-yellow-500/50 rounded-lg text-yellow-400 text-xs">
          Backend model not loaded (using mock mode)
        </div>
      )}
    </>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
