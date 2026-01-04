/**
 * Re-segment Confirmation Dialog
 *
 * Shows when the user views a document that was segmented with an older
 * configuration version. Offers to re-run segmentation with current settings.
 */

import { useState } from 'react';
import { ArrowPathIcon, ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface ResegmentDialogProps {
  isOpen: boolean;
  documentName: string;
  oldVersion: number | undefined;
  currentVersion: number;
  onResegment: () => Promise<void>;
  onDismiss: () => void;
}

export default function ResegmentDialog({
  isOpen,
  documentName,
  oldVersion,
  currentVersion,
  onResegment,
  onDismiss,
}: ResegmentDialogProps) {
  const [isResegmenting, setIsResegmenting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleResegment = async () => {
    setIsResegmenting(true);
    setError(null);
    try {
      await onResegment();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Re-segmentation failed');
      setIsResegmenting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 max-w-lg w-full mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
              <ExclamationTriangleIcon className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Configuration Changed</h2>
              <p className="text-sm text-slate-400">Re-segment to apply new settings</p>
            </div>
          </div>
          <button
            onClick={onDismiss}
            disabled={isResegmenting}
            className="text-slate-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="mb-6 space-y-3">
          <p className="text-slate-300">
            The document "<span className="font-medium text-white">{documentName}</span>" was
            segmented with an older configuration.
          </p>

          <div className="flex items-center gap-4 p-3 bg-slate-900/50 rounded-lg">
            <div className="flex-1">
              <div className="text-xs text-slate-500 mb-1">Document segmented with</div>
              <div className="text-sm font-medium text-slate-300">
                Config Version {oldVersion ?? 'Unknown'}
              </div>
            </div>
            <div className="text-slate-600">→</div>
            <div className="flex-1">
              <div className="text-xs text-slate-500 mb-1">Current config</div>
              <div className="text-sm font-medium text-blue-400">Version {currentVersion}</div>
            </div>
          </div>

          <p className="text-sm text-slate-400">
            Re-segmenting will apply your current prompt settings and detection thresholds to this
            document.
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={handleResegment}
            disabled={isResegmenting}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isResegmenting ? (
              <>
                <ArrowPathIcon className="w-4 h-4 animate-spin" />
                Re-segmenting...
              </>
            ) : (
              <>
                <ArrowPathIcon className="w-4 h-4" />
                Re-segment Now
              </>
            )}
          </button>
          <button
            onClick={onDismiss}
            disabled={isResegmenting}
            className="px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors disabled:opacity-50"
          >
            Keep Current
          </button>
        </div>
      </div>
    </div>
  );
}
