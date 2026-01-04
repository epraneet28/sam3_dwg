/**
 * MinimalTopBar Component for SAM3
 * Simplified version from docling-interactive
 */

import { ChevronLeftIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

export const TOP_BAR_STYLES = {
  container: 'flex items-center justify-between bg-slate-800/50 backdrop-blur-sm border-b border-slate-700 px-4 py-2',
  navButton: 'p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors',
  title: 'text-base font-medium text-white truncate',
  subtitle: 'text-xs text-slate-400 truncate',
};

interface MinimalTopBarProps {
  /** Title to display */
  title: string;
  /** Optional subtitle (e.g., "5 pages") */
  subtitle?: string;
  /** Callback for back button */
  onBack?: () => void;
  /** Action buttons to render on the right */
  actions?: React.ReactNode;
  /** Additional className for container */
  className?: string;
}

export function MinimalTopBar({
  title,
  subtitle,
  onBack,
  actions,
  className,
}: MinimalTopBarProps) {
  return (
    <div className={clsx(TOP_BAR_STYLES.container, className)}>
      {/* Left section: Navigation + Title */}
      <div className="flex items-center gap-3 min-w-0 flex-1">
        {/* Back button */}
        {onBack && (
          <button
            onClick={onBack}
            className={TOP_BAR_STYLES.navButton}
            title="Back to Dashboard"
          >
            <ChevronLeftIcon className="w-5 h-5" />
          </button>
        )}

        {/* Title and subtitle */}
        <div className="min-w-0">
          <h2 className={TOP_BAR_STYLES.title}>{title}</h2>
          {subtitle && (
            <p className={TOP_BAR_STYLES.subtitle}>{subtitle}</p>
          )}
        </div>
      </div>

      {/* Right section: Actions */}
      {actions && (
        <div className="flex items-center gap-2 flex-shrink-0">
          {actions}
        </div>
      )}
    </div>
  );
}
