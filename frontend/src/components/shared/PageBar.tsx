/**
 * PageBar Component for SAM3
 * Simplified page navigation with zoom controls
 */

import { ChevronLeftIcon, ChevronRightIcon, MagnifyingGlassPlusIcon, MagnifyingGlassMinusIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

export const PAGE_BAR_STYLES = {
  container: 'flex items-center justify-between bg-slate-800/50 backdrop-blur-sm border-b border-slate-700 px-4 py-2',
  section: 'flex items-center gap-2',
  button: 'p-1.5 rounded text-slate-400 hover:text-white hover:bg-slate-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed',
  input: 'w-16 px-2 py-1 text-sm text-center bg-slate-700 border border-slate-600 text-white rounded focus:outline-none focus:ring-1 focus:ring-blue-500',
  text: 'text-sm text-slate-400',
};

interface PageBarProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  zeroIndexed?: boolean;
  zoomControls?: {
    zoom: number;
    onZoomIn: () => void;
    onZoomOut: () => void;
    onFitToPage: () => void;
  };
}

export function PageBar({
  currentPage,
  totalPages,
  onPageChange,
  zeroIndexed = false,
  zoomControls,
}: PageBarProps) {
  // Convert between 0-indexed (internal) and 1-indexed (display)
  const displayPage = zeroIndexed ? currentPage + 1 : currentPage;
  const handlePageInput = (value: string) => {
    const num = parseInt(value, 10);
    if (!isNaN(num)) {
      const targetPage = zeroIndexed ? num - 1 : num;
      if (targetPage >= 0 && targetPage < totalPages) {
        onPageChange(targetPage);
      }
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 0) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages - 1) {
      onPageChange(currentPage + 1);
    }
  };

  return (
    <div className={PAGE_BAR_STYLES.container}>
      {/* Left: Zoom controls */}
      <div className={PAGE_BAR_STYLES.section}>
        {zoomControls && (
          <>
            <button
              onClick={zoomControls.onZoomOut}
              className={PAGE_BAR_STYLES.button}
              title="Zoom out"
            >
              <MagnifyingGlassMinusIcon className="w-4 h-4" />
            </button>
            <span className={PAGE_BAR_STYLES.text}>
              {Math.round(zoomControls.zoom * 100)}%
            </span>
            <button
              onClick={zoomControls.onZoomIn}
              className={PAGE_BAR_STYLES.button}
              title="Zoom in"
            >
              <MagnifyingGlassPlusIcon className="w-4 h-4" />
            </button>
            <button
              onClick={zoomControls.onFitToPage}
              className={clsx(PAGE_BAR_STYLES.button, 'px-2 text-xs')}
              title="Fit to page"
            >
              Fit
            </button>
          </>
        )}
      </div>

      {/* Center: Page navigation */}
      <div className={PAGE_BAR_STYLES.section}>
        <button
          onClick={handlePrevPage}
          disabled={currentPage === 0}
          className={PAGE_BAR_STYLES.button}
          title="Previous page"
        >
          <ChevronLeftIcon className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2">
          <input
            type="number"
            min="1"
            max={totalPages}
            value={displayPage}
            onChange={(e) => handlePageInput(e.target.value)}
            className={PAGE_BAR_STYLES.input}
          />
          <span className={PAGE_BAR_STYLES.text}>of {totalPages}</span>
        </div>

        <button
          onClick={handleNextPage}
          disabled={currentPage === totalPages - 1}
          className={PAGE_BAR_STYLES.button}
          title="Next page"
        >
          <ChevronRightIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Right: Placeholder for future controls */}
      <div className={PAGE_BAR_STYLES.section}>
        {/* Empty for now */}
      </div>
    </div>
  );
}
