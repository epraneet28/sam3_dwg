import { useState, useMemo, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useStore, useDocuments, useConfigVersion } from '../store';
import { MinimalTopBar, PageBar, ControlsHint } from '../components/shared';
import { DrawingCanvas, ZoneSidebar, ZoneDetailsModal, ResegmentDialog } from '../components/viewer';
import { Button } from '../components/ui/Button';
import { DEFAULT_CONFIDENCE_THRESHOLD, ZONE_TYPES } from '../utils/constants';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { useZoomPan } from '../hooks/useZoomPan';
import { exportAsJSON, exportAsCSV, downloadFile } from '../utils/exportZones';
import { api } from '../api/client';
import type { ShortcutConfig } from '../hooks/useKeyboardShortcuts';
import type { ZoneType } from '../types';

export default function Viewer() {
  const { docId } = useParams<{ docId: string }>();
  const navigate = useNavigate();
  const documents = useDocuments();
  const configVersion = useConfigVersion();
  const { updateDocument } = useStore();

  const document = documents.find((d) => d.id === docId);

  // Filter documents to segmented ones for the dropdown
  const segmentedDocs = useMemo(() => {
    return documents.filter((d) => d.status === 'segmented');
  }, [documents]);

  // Handle document selection from dropdown
  const handleSelectDocument = (newDocId: string) => {
    if (newDocId && newDocId !== docId) {
      // Reset state when switching documents
      setCurrentPage(0);
      setSelectedZoneId(null);
      setHoveredZoneId(null);
      setHiddenZoneIds(new Set());
      setDetailsZone(null);
      setResegmentDismissed(false);
      navigate(`/viewer/${newDocId}`);
    }
  };

  // Config change detection
  const configChanged = useMemo(() => {
    if (!document) return false;
    // If document was segmented with an older config, show dialog
    return document.configVersionUsed !== undefined && document.configVersionUsed < configVersion;
  }, [document, configVersion]);

  // Resegment dialog state
  const [showResegmentDialog, setShowResegmentDialog] = useState(false);
  const [resegmentDismissed, setResegmentDismissed] = useState(false);

  // Show resegment dialog when config has changed (but only once per session)
  useEffect(() => {
    if (configChanged && !resegmentDismissed && document?.status === 'segmented') {
      setShowResegmentDialog(true);
    }
  }, [configChanged, resegmentDismissed, document?.status]);

  // Handle resegmentation
  const handleResegment = async () => {
    if (!docId) return;

    try {
      const segmentResult = await api.segmentDocument(docId);

      // Update document with new segmentation results
      // Fetch image URLs asynchronously
      const pages = await Promise.all(
        segmentResult.pages.map(async (p) => ({
          pageNumber: p.pageNumber,
          imageUrl: await api.getPageImageUrl(docId, p.pageNumber),
          zones: p.zones,
          pageType: p.pageType,
          processingTimeMs: p.processingTimeMs,
        }))
      );

      updateDocument(docId, {
        status: 'segmented',
        configVersionUsed: configVersion,
        pages,
      });

      setShowResegmentDialog(false);
      setResegmentDismissed(true);
    } catch (error) {
      throw error;
    }
  };

  const handleDismissResegment = () => {
    setShowResegmentDialog(false);
    setResegmentDismissed(true);
  };

  // Page state
  const [currentPage, setCurrentPage] = useState(0);

  // Image dimensions tracking
  const [imageDimensions, setImageDimensions] = useState<{ width: number; height: number } | null>(
    null
  );

  // Production-grade zoom/pan hook (matching docling-interactive)
  const {
    zoom,
    pan,
    isPanning,
    isZooming,
    handleZoomIn,
    handleZoomOut,
    handleFitToPage,
    handleFitToWidth,
    handleActualSize,
    handlePanStart,
    handlePanMove,
    handlePanEnd,
    handleDoubleClick,
    containerRef,
  } = useZoomPan({ imageDimensions });

  // Filter state
  const [confidenceThreshold, setConfidenceThreshold] = useState(DEFAULT_CONFIDENCE_THRESHOLD);
  const [selectedZoneTypes, setSelectedZoneTypes] = useState<Set<ZoneType>>(new Set(ZONE_TYPES));

  // Selection state
  const [hoveredZoneId, setHoveredZoneId] = useState<string | null>(null);
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);

  // Hidden zones state (zones hidden from viewer but still in sidebar)
  const [hiddenZoneIds, setHiddenZoneIds] = useState<Set<string>>(new Set());

  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Mask display state
  const [showMasks, setShowMasks] = useState(true);

  // Export modal state
  const [showExportModal, setShowExportModal] = useState(false);
  const [includeConfidence, setIncludeConfidence] = useState(true);
  const [includeCoordinates, setIncludeCoordinates] = useState(true);

  // Zone details modal state
  const [detailsZone, setDetailsZone] = useState<string | null>(null);

  if (!document) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-2">Document Not Found</h1>
          <p className="text-slate-400 mb-4">The document you're looking for doesn't exist.</p>
          <Button onClick={() => navigate('/')}>Return to Dashboard</Button>
        </div>
      </div>
    );
  }

  const currentPageData = document.pages[currentPage];
  if (!currentPageData) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-2">Page Not Found</h1>
          <p className="text-slate-400 mb-4">This page hasn't been processed yet.</p>
          <Button onClick={() => navigate('/')}>Return to Dashboard</Button>
        </div>
      </div>
    );
  }

  // Filter zones by confidence only (for counting in sidebar)
  const confidenceFilteredZones = useMemo(() => {
    return currentPageData.zones.filter(
      (zone) => zone.confidence >= confidenceThreshold
    );
  }, [currentPageData.zones, confidenceThreshold]);

  // Filter zones by confidence and type (for display)
  const filteredZones = useMemo(() => {
    return confidenceFilteredZones.filter(
      (zone) => selectedZoneTypes.has(zone.zone_type)
    );
  }, [confidenceFilteredZones, selectedZoneTypes]);


  const handleZoneTypeToggle = (type: ZoneType) => {
    setSelectedZoneTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  const handleSelectAllTypes = () => {
    setSelectedZoneTypes(new Set(ZONE_TYPES));
  };

  const handleDeselectAllTypes = () => {
    setSelectedZoneTypes(new Set());
  };

  // Toggle zone visibility on the canvas
  const handleToggleZoneVisibility = (zoneId: string) => {
    setHiddenZoneIds((prev) => {
      const next = new Set(prev);
      if (next.has(zoneId)) {
        next.delete(zoneId);
      } else {
        next.add(zoneId);
      }
      return next;
    });
  };

  // Keyboard shortcuts
  const shortcuts: ShortcutConfig[] = useMemo(
    () => [
      {
        key: 'ArrowLeft',
        handler: () => {
          if (currentPage > 0) {
            setCurrentPage(currentPage - 1);
          }
        },
        description: 'Previous page',
        preventDefault: true,
      },
      {
        key: 'ArrowRight',
        handler: () => {
          if (currentPage < document.totalPages - 1) {
            setCurrentPage(currentPage + 1);
          }
        },
        description: 'Next page',
        preventDefault: true,
      },
      {
        key: 'Escape',
        handler: () => {
          setSelectedZoneId(null);
          setDetailsZone(null);
        },
        description: 'Deselect zone / Close modal',
      },
      {
        key: '+',
        handler: handleZoomIn,
        description: 'Zoom in',
        preventDefault: true,
      },
      {
        key: '=', // Also + without shift
        handler: handleZoomIn,
        description: 'Zoom in (alt)',
        preventDefault: true,
      },
      {
        key: '-',
        handler: handleZoomOut,
        description: 'Zoom out',
        preventDefault: true,
      },
      {
        key: '0',
        handler: handleFitToPage,
        description: 'Fit to page',
        preventDefault: true,
      },
      {
        key: '1',
        handler: handleActualSize,
        description: 'Actual size (100%)',
        preventDefault: true,
      },
      {
        key: '2',
        handler: handleFitToWidth,
        description: 'Fit to width',
        preventDefault: true,
      },
    ],
    [currentPage, document.totalPages, handleZoomIn, handleZoomOut, handleFitToPage, handleActualSize, handleFitToWidth]
  );

  useKeyboardShortcuts(shortcuts);

  const totalZones = currentPageData.zones.length;

  // Filter out hidden zones for canvas display
  const visibleZones = useMemo(() => {
    return filteredZones.filter((zone) => !hiddenZoneIds.has(zone.zone_id));
  }, [filteredZones, hiddenZoneIds]);

  // Find zone for details modal
  const zoneForDetails = detailsZone
    ? filteredZones.find((z) => z.zone_id === detailsZone) || null
    : null;

  return (
    <div className="flex flex-col h-screen bg-slate-900">
      {/* Top Bar */}
      <MinimalTopBar
        title="Viewer"
        subtitle={`${document.totalPages} ${document.totalPages === 1 ? 'page' : 'pages'} • ${totalZones} ${totalZones === 1 ? 'zone' : 'zones'} detected`}
        onBack={() => navigate('/')}
        centerContent={
          <select
            value={docId || ''}
            onChange={(e) => handleSelectDocument(e.target.value)}
            className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500 w-full min-w-[200px] max-w-[350px]"
            title="Switch document"
          >
            {segmentedDocs.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.name}
              </option>
            ))}
          </select>
        }
        actions={
          <div className="flex items-center gap-2">
            {/* Config Changed Badge */}
            {configChanged && resegmentDismissed && (
              <button
                onClick={() => setShowResegmentDialog(true)}
                className="px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 text-sm rounded-lg transition-colors flex items-center gap-2 border border-amber-500/50"
                title="Settings have changed - click to re-segment"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className="hidden sm:inline">Settings Changed</span>
              </button>
            )}
            <button
              onClick={() => setShowExportModal(true)}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
              title="Export zones"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span className="hidden sm:inline">Export</span>
            </button>
          </div>
        }
      />

      {/* Page Bar */}
      {document.totalPages > 1 && (
        <PageBar
          currentPage={currentPage}
          totalPages={document.totalPages}
          onPageChange={setCurrentPage}
          zeroIndexed={true}
          zoomControls={{
            zoom,
            onZoomIn: handleZoomIn,
            onZoomOut: handleZoomOut,
            onFitToPage: handleFitToPage,
          }}
        />
      )}

      {/* Main Content - Canvas takes full width, sidebar floats */}
      <div className="flex-1 relative overflow-hidden">
        {/* Canvas - Always full width */}
        <div className="flex-1 flex flex-col bg-slate-950">
          <DrawingCanvas
            imageUrl={currentPageData.imageUrl}
            zones={visibleZones}
            zoom={zoom}
            pan={pan}
            isPanning={isPanning}
            isZooming={isZooming}
            hoveredZoneId={hoveredZoneId}
            selectedZoneId={selectedZoneId}
            showMasks={showMasks}
            onZoneClick={setSelectedZoneId}
            onZoneHover={setHoveredZoneId}
            onPanStart={handlePanStart}
            onPanMove={handlePanMove}
            onPanEnd={handlePanEnd}
            onDoubleClick={handleDoubleClick}
            onImageLoad={(dims) => setImageDimensions(dims)}
            containerRef={containerRef}
          />

          <ControlsHint />
        </div>

        {/* Floating Zone Sidebar */}
        <ZoneSidebar
          zones={filteredZones}
          allZonesForCounting={confidenceFilteredZones}
          confidenceThreshold={confidenceThreshold}
          selectedZoneTypes={selectedZoneTypes}
          hoveredZoneId={hoveredZoneId}
          selectedZoneId={selectedZoneId}
          hiddenZoneIds={hiddenZoneIds}
          showMasks={showMasks}
          isOpen={sidebarOpen}
          onOpenChange={setSidebarOpen}
          onThresholdChange={setConfidenceThreshold}
          onZoneTypeToggle={handleZoneTypeToggle}
          onSelectAllTypes={handleSelectAllTypes}
          onDeselectAllTypes={handleDeselectAllTypes}
          onZoneClick={setSelectedZoneId}
          onZoneHover={setHoveredZoneId}
          onZoneDetails={setDetailsZone}
          onToggleZoneVisibility={handleToggleZoneVisibility}
          onShowMasksChange={setShowMasks}
        />
      </div>

      {/* Zone Details Modal */}
      <ZoneDetailsModal zone={zoneForDetails} onClose={() => setDetailsZone(null)} />

      {/* Resegment Dialog */}
      <ResegmentDialog
        isOpen={showResegmentDialog}
        documentName={document.name}
        oldVersion={document.configVersionUsed}
        currentVersion={configVersion}
        onResegment={handleResegment}
        onDismiss={handleDismissResegment}
      />

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 max-w-md w-full mx-4">
            <h2 className="text-lg font-semibold text-white mb-4">Export Zones</h2>

            <div className="space-y-3 mb-6">
              <label className="flex items-center gap-3 text-slate-300 cursor-pointer hover:text-white transition-colors">
                <input
                  type="checkbox"
                  checked={includeConfidence}
                  onChange={(e) => setIncludeConfidence(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-2 focus:ring-blue-500"
                />
                Include confidence scores
              </label>
              <label className="flex items-center gap-3 text-slate-300 cursor-pointer hover:text-white transition-colors">
                <input
                  type="checkbox"
                  checked={includeCoordinates}
                  onChange={(e) => setIncludeCoordinates(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-2 focus:ring-blue-500"
                />
                Include bounding box coordinates
              </label>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  try {
                    // Validate document has pages
                    if (!document.pages || document.pages.length === 0) {
                      alert('No pages to export');
                      return;
                    }

                    const content = exportAsJSON(document, {
                      includeConfidence,
                      includeCoordinates,
                    });
                    downloadFile(content, `${document.name}_zones.json`, 'application/json');
                    setShowExportModal(false);
                  } catch (error) {
                    console.error('Export failed:', error);
                    alert('Export failed. Please try again.');
                  }
                }}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
              >
                JSON
              </button>
              <button
                onClick={() => {
                  try {
                    // Validate document has pages
                    if (!document.pages || document.pages.length === 0) {
                      alert('No pages to export');
                      return;
                    }

                    const content = exportAsCSV(document, {
                      includeConfidence,
                      includeCoordinates,
                    });
                    downloadFile(content, `${document.name}_zones.csv`, 'text/csv');
                    setShowExportModal(false);
                  } catch (error) {
                    console.error('Export failed:', error);
                    alert('Export failed. Please try again.');
                  }
                }}
                className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium"
              >
                CSV
              </button>
              <button
                onClick={() => setShowExportModal(false)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
