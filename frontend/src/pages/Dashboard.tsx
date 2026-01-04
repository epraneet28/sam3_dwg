import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MagnifyingGlassIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { useStore, useDocuments, useDashboardSearch, useConfigVersion } from '../store';
import { UploadZone, DocumentCard } from '../components/dashboard';
import { api } from '../api/client';
import type { SAM3Document } from '../types';

export default function Dashboard() {
  const navigate = useNavigate();
  const documents = useDocuments();
  const searchTerm = useDashboardSearch();
  const configVersion = useConfigVersion();
  const { setDashboardSearch, addDocument, deleteDocument: removeDocument, updateDocument } = useStore();

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Filter documents by search term
  const filteredDocs = documents.filter((doc) =>
    doc.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleUpload = async (file: File) => {
    setUploading(true);
    setUploadError(null);

    try {
      // 1. Upload file (mock - stores in localStorage)
      const { docId, totalPages } = await api.uploadDocument(file);

      // 2. Create document in store
      const newDoc: SAM3Document = {
        id: docId,
        name: file.name,
        uploadedAt: new Date().toISOString(),
        totalPages,
        size: file.size,
        status: 'pending',
        pages: [],
      };
      addDocument(newDoc);

      // 3. Auto-segment
      try {
        const segmentResult = await api.segmentDocument(docId);

        // 4. Update document with segmentation results
        updateDocument(docId, {
          status: 'segmented',
          configVersionUsed: configVersion, // Track which config was used
          pages: segmentResult.pages.map((p) => ({
            pageNumber: p.pageNumber,
            imageUrl: api.getPageImageUrl(docId, p.pageNumber),
            zones: p.zones,
            pageType: p.pageType,
            processingTimeMs: p.processingTimeMs,
          })),
        });

        // 5. Navigate to viewer
        navigate(`/viewer/${docId}`);
      } catch (segmentError) {
        updateDocument(docId, {
          status: 'error',
          error: segmentError instanceof Error ? segmentError.message : 'Segmentation failed',
        });
        setUploadError('Failed to segment document. You can view it anyway.');
      }
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (doc: SAM3Document) => {
    if (!confirm(`Delete "${doc.name}"?`)) return;

    try {
      await api.deleteDocument(doc.id);
      removeDocument(doc.id);
      setUploadError(null); // Clear any previous errors on success
    } catch (error) {
      setUploadError('Failed to delete document');
    }
  };

  const handleRefresh = () => {
    // For now, just clear search - documents are in Zustand store
    setDashboardSearch('');
  };

  return (
    <div className="h-full overflow-y-auto bg-slate-900 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">SAM3 Drawing Segmenter</h1>
          <p className="text-sm text-slate-400">Upload engineering drawings for automatic zone segmentation</p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
        >
          <ArrowPathIcon className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Upload Zone */}
      <div className="mb-6">
        <UploadZone onUpload={handleUpload} uploading={uploading} />
        {uploadError && (
          <div className="mt-2 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
            {uploadError}
          </div>
        )}
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search drawings..."
            value={searchTerm}
            onChange={(e) => setDashboardSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Document Grid */}
      {filteredDocs.length > 0 ? (
        <>
          <div className="mb-4 text-sm text-slate-400">
            {filteredDocs.length} {filteredDocs.length === 1 ? 'drawing' : 'drawings'}
            {searchTerm && ` matching "${searchTerm}"`}
          </div>
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredDocs.map((doc) => (
              <DocumentCard
                key={doc.id}
                document={doc}
                onClick={() => navigate(`/viewer/${doc.id}`)}
                onDelete={() => handleDelete(doc)}
              />
            ))}
          </div>
        </>
      ) : (
        <div className="text-center py-16">
          <div className="text-slate-500 mb-2">
            {searchTerm ? `No drawings found matching "${searchTerm}"` : 'No drawings uploaded yet'}
          </div>
          {searchTerm && (
            <button
              onClick={() => setDashboardSearch('')}
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              Clear search
            </button>
          )}
        </div>
      )}
    </div>
  );
}
