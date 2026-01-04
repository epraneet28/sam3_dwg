/**
 * Standard panel header component
 * Based on docling-interactive pattern
 */

import { XMarkIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface PanelHeaderProps {
  title: string;
  count?: number;
  countLabel?: string;
  instruction?: string;
  onClose?: () => void;
  closeIcon?: 'x' | 'chevron';
  children?: React.ReactNode;
}

export default function PanelHeader({
  title,
  count,
  countLabel = 'items',
  instruction,
  onClose,
  closeIcon = 'x',
  children,
}: PanelHeaderProps) {
  // Auto-singularize label
  const displayLabel = count === 1 && countLabel.endsWith('s')
    ? countLabel.slice(0, -1)
    : countLabel;

  const CloseIcon = closeIcon === 'chevron' ? ChevronRightIcon : XMarkIcon;
  const closeTitle = closeIcon === 'chevron' ? 'Collapse panel' : 'Close panel';

  return (
    <div className="flex-shrink-0 px-4 py-3 border-b border-slate-700 bg-slate-800/80">
      {/* Title Row */}
      <div className="flex items-center justify-between gap-3 mb-1">
        <div className="flex items-center gap-2 min-w-0">
          <h2 className="text-base font-semibold text-white truncate">
            {title}
          </h2>
          {count !== undefined && (
            <span className="flex-shrink-0 text-sm text-slate-400">
              {count} {displayLabel}
            </span>
          )}
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="flex-shrink-0 p-1 text-slate-400 hover:text-white hover:bg-white/5 rounded transition-colors"
            title={closeTitle}
          >
            <CloseIcon className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Instruction Text */}
      {instruction && (
        <p className="text-xs text-slate-500">
          {instruction}
        </p>
      )}

      {/* Optional children (filters, controls, etc.) */}
      {children}
    </div>
  );
}
