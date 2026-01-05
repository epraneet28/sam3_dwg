/**
 * SmartSelectPanel - Roboflow-style Smart Select UI
 *
 * Provides:
 * - Polygon/Pixels output toggle
 * - Refinement instructions
 * - Undo/Redo buttons
 * - Delete/Finish actions
 * - Polygon complexity slider (when in polygon mode)
 */

import { useEffect, useMemo } from 'react';
import {
  XMarkIcon,
  ArrowUturnLeftIcon,
  ArrowUturnRightIcon,
  TrashIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import type {
  SmartSelectOutputMode,
  SmartSelectState,
  MaskCandidate,
  PolygonData,
} from '../../types';

interface SmartSelectPanelProps {
  // State
  isOpen: boolean;
  onClose: () => void;
  selectState: SmartSelectState;
  outputMode: SmartSelectOutputMode;
  onOutputModeChange: (mode: SmartSelectOutputMode) => void;

  // Mask/Polygon data
  currentMask: MaskCandidate | null;
  currentPolygon: PolygonData | null;
  maskCandidates: MaskCandidate[];
  selectedMaskIndex: number;
  onSelectMask: (index: number) => void;

  // Polygon settings
  polygonComplexity: number;
  onPolygonComplexityChange: (complexity: number) => void;

  // History
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;

  // Actions
  onDelete: () => void;
  onFinish: () => void;
  isRunning?: boolean;
}

export function SmartSelectPanel({
  isOpen,
  onClose,
  selectState,
  outputMode,
  onOutputModeChange,
  currentMask,
  currentPolygon,
  maskCandidates,
  selectedMaskIndex,
  onSelectMask,
  polygonComplexity,
  onPolygonComplexityChange,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  onDelete,
  onFinish,
  isRunning = false,
}: SmartSelectPanelProps) {
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't handle if typing in input
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'TEXTAREA'
      ) {
        return;
      }

      // Enter to finish
      if (e.key === 'Enter' && currentMask) {
        e.preventDefault();
        onFinish();
      }

      // Ctrl+Z to undo
      if (e.key === 'z' && (e.ctrlKey || e.metaKey) && !e.shiftKey && canUndo) {
        e.preventDefault();
        onUndo();
      }

      // Ctrl+Shift+Z or Ctrl+Y to redo
      if (
        ((e.key === 'z' && e.shiftKey) || e.key === 'y') &&
        (e.ctrlKey || e.metaKey) &&
        canRedo
      ) {
        e.preventDefault();
        onRedo();
      }

      // Delete/Backspace to delete
      if ((e.key === 'Delete' || e.key === 'Backspace') && currentMask) {
        e.preventDefault();
        onDelete();
      }
    };

    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, currentMask, canUndo, canRedo, onUndo, onRedo, onDelete, onFinish]);

  // Instruction text based on state
  const instructionText = useMemo(() => {
    switch (selectState) {
      case 'idle':
        return 'Click on an object or draw a box to select it.';
      case 'initial':
      case 'refining':
        return 'Click outside to add to selection, inside to remove.';
      case 'confirmed':
        return 'Selection confirmed. Start a new selection or export.';
      default:
        return '';
    }
  }, [selectState]);

  // Stats for current selection
  const selectionStats = useMemo(() => {
    if (outputMode === 'polygon' && currentPolygon) {
      return {
        label: 'Polygon',
        detail: `${currentPolygon.points.length} vertices`,
      };
    }
    if (currentMask) {
      const width = currentMask.bbox[2] - currentMask.bbox[0];
      const height = currentMask.bbox[3] - currentMask.bbox[1];
      return {
        label: 'Mask',
        detail: `${Math.round(width)} × ${Math.round(height)} px`,
      };
    }
    return null;
  }, [outputMode, currentMask, currentPolygon]);

  if (!isOpen) return null;

  return (
    <div className="w-full bg-slate-800/95 backdrop-blur-sm border border-slate-700 rounded-xl shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-emerald-400">Smart Select</h3>
        <button
          onClick={onClose}
          className="p-1 text-slate-400 hover:text-white transition-colors rounded hover:bg-slate-700"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Model indicator (static for now) */}
        <div>
          <label className="block text-[10px] uppercase tracking-wide text-slate-500 mb-1.5">
            Model
          </label>
          <div className="flex items-center gap-2 px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg">
            <span className="text-sm text-white font-medium">SAM3</span>
            <span className="ml-auto text-[10px] text-slate-500">v2.1</span>
          </div>
        </div>

        {/* Output Mode Toggle */}
        <div>
          <label className="block text-[10px] uppercase tracking-wide text-slate-500 mb-1.5">
            Output Format
          </label>
          <div className="flex rounded-lg overflow-hidden border border-slate-600">
            <button
              onClick={() => onOutputModeChange('polygon')}
              className={`flex-1 px-4 py-2 text-xs font-medium transition-colors ${
                outputMode === 'polygon'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-slate-700 text-slate-400 hover:bg-slate-600 hover:text-white'
              }`}
            >
              Polygon
            </button>
            <button
              onClick={() => onOutputModeChange('pixels')}
              className={`flex-1 px-4 py-2 text-xs font-medium transition-colors ${
                outputMode === 'pixels'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-slate-700 text-slate-400 hover:bg-slate-600 hover:text-white'
              }`}
            >
              Pixels
            </button>
          </div>
        </div>

        {/* Instructions */}
        <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-700">
          <div className="flex items-start gap-2">
            <div className="w-4 h-4 mt-0.5 rounded-full bg-slate-600 flex items-center justify-center">
              <span className="text-[10px] text-slate-300">i</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {instructionText}
            </p>
          </div>
        </div>

        {/* Polygon Complexity (only in polygon mode) */}
        {outputMode === 'polygon' && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-[10px] uppercase tracking-wide text-slate-500">
                Complexity
              </label>
              <span className="text-xs text-slate-400 tabular-nums">
                {Math.round(polygonComplexity * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={polygonComplexity}
              onChange={(e) => onPolygonComplexityChange(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-700 rounded-full appearance-none cursor-pointer
                [&::-webkit-slider-thumb]:appearance-none
                [&::-webkit-slider-thumb]:w-3
                [&::-webkit-slider-thumb]:h-3
                [&::-webkit-slider-thumb]:rounded-full
                [&::-webkit-slider-thumb]:bg-emerald-500
                [&::-webkit-slider-thumb]:cursor-pointer
                [&::-webkit-slider-thumb]:transition-transform
                [&::-webkit-slider-thumb]:hover:scale-110"
            />
            <div className="flex justify-between mt-1">
              <span className="text-[10px] text-slate-600">Simplified</span>
              <span className="text-[10px] text-slate-600">Detailed</span>
            </div>
          </div>
        )}

        {/* Mask Candidates (when available) */}
        {maskCandidates.length > 1 && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-[10px] uppercase tracking-wide text-slate-500">
                Mask Options
              </label>
              <span className="text-xs text-slate-400">
                {selectedMaskIndex + 1} / {maskCandidates.length}
              </span>
            </div>
            <div className="flex gap-1.5">
              {maskCandidates.map((mask, idx) => (
                <button
                  key={idx}
                  onClick={() => onSelectMask(idx)}
                  className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                    selectedMaskIndex === idx
                      ? 'bg-emerald-600 text-white'
                      : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700 hover:text-white'
                  }`}
                  title={`IoU: ${(mask.iou_score * 100).toFixed(1)}%`}
                >
                  {(mask.iou_score * 100).toFixed(0)}%
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Selection Stats */}
        {selectionStats && (
          <div className="flex items-center justify-between px-3 py-2 bg-emerald-900/20 border border-emerald-500/30 rounded-lg">
            <span className="text-xs text-emerald-300">{selectionStats.label}</span>
            <span className="text-xs text-emerald-400 font-mono">{selectionStats.detail}</span>
          </div>
        )}

        {/* Undo/Redo */}
        <div className="flex gap-2">
          <button
            onClick={onUndo}
            disabled={!canUndo || isRunning}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:text-slate-600 text-slate-300 rounded-lg text-xs font-medium transition-colors"
            title="Undo (Ctrl+Z)"
          >
            <ArrowUturnLeftIcon className="w-3.5 h-3.5" />
            Undo
          </button>
          <button
            onClick={onRedo}
            disabled={!canRedo || isRunning}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:text-slate-600 text-slate-300 rounded-lg text-xs font-medium transition-colors"
            title="Redo (Ctrl+Shift+Z)"
          >
            <ArrowUturnRightIcon className="w-3.5 h-3.5" />
            Redo
          </button>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2 border-t border-slate-700">
          <button
            onClick={onDelete}
            disabled={!currentMask || isRunning}
            className="flex items-center justify-center gap-1.5 px-3 py-2.5 text-red-400 hover:text-red-300 hover:bg-red-500/10 disabled:text-slate-600 disabled:hover:bg-transparent rounded-lg text-xs font-medium transition-colors"
            title="Delete selection"
          >
            <TrashIcon className="w-4 h-4" />
            Delete
          </button>
          <button
            onClick={onFinish}
            disabled={!currentMask || isRunning}
            className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg text-sm font-medium transition-colors"
            title="Finish selection (Enter)"
          >
            <CheckIcon className="w-4 h-4" />
            Finish (Enter)
          </button>
        </div>
      </div>
    </div>
  );
}

export default SmartSelectPanel;
