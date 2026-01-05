/**
 * MinimalTopBar Component for SAM3
 * Simplified version from docling-interactive
 *
 * Supports true center alignment using CSS Grid:
 * - Left section: Navigation + Title (left-aligned)
 * - Center section: Optional centered content (truly centered based on bar width)
 * - Right section: Action buttons (right-aligned)
 *
 * The center content is truly centered regardless of left/right content width.
 * On smaller screens, the layout becomes responsive to prevent overlap.
 */

import { ChevronLeftIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

export const TOP_BAR_STYLES = {
  container:
    'bg-slate-800/50 backdrop-blur-sm border-b border-slate-700 px-4 py-2',
  navButton:
    'p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors',
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
  /** Content to render in the true center (optional) */
  centerContent?: React.ReactNode;
  /** Additional className for container */
  className?: string;
}

export function MinimalTopBar({
  title,
  subtitle,
  onBack,
  actions,
  centerContent,
  className,
}: MinimalTopBarProps) {
  // Use CSS Grid for true centering when centerContent is provided
  if (centerContent) {
    return (
      <div
        className={clsx(
          TOP_BAR_STYLES.container,
          // CSS Grid with 3 equal columns for true centering
          // minmax(0, 1fr) prevents content from pushing center off-center
          'grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2',
          className
        )}
      >
        {/* Left section: Navigation + Title */}
        <div className="flex items-center gap-3 min-w-0 justify-self-start">
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
          <div className="min-w-0 hidden sm:block">
            <h2 className={TOP_BAR_STYLES.title}>{title}</h2>
            {subtitle && <p className={TOP_BAR_STYLES.subtitle}>{subtitle}</p>}
          </div>
        </div>

        {/* Center section: Truly centered content */}
        <div className="flex items-center justify-center min-w-0 max-w-full">
          {centerContent}
        </div>

        {/* Right section: Actions */}
        <div className="flex items-center gap-2 justify-self-end flex-shrink-0">
          {actions}
        </div>
      </div>
    );
  }

  // Original flexbox layout when no center content
  return (
    <div className={clsx(TOP_BAR_STYLES.container, 'flex items-center justify-between', className)}>
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
          {subtitle && <p className={TOP_BAR_STYLES.subtitle}>{subtitle}</p>}
        </div>
      </div>

      {/* Right section: Actions */}
      {actions && (
        <div className="flex items-center gap-2 flex-shrink-0">{actions}</div>
      )}
    </div>
  );
}
