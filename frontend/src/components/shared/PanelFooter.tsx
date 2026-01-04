/**
 * Standard panel footer component
 * Based on docling-interactive pattern
 */

interface PanelFooterProps {
  pageCount?: number;
  pageCountUnit?: string;
  pageCountSuffix?: string;
  status?: string;
  children?: React.ReactNode;
}

export default function PanelFooter({
  pageCount,
  pageCountUnit = 'items',
  pageCountSuffix = 'on this page',
  status,
  children,
}: PanelFooterProps) {
  // Auto-singularize unit
  const displayUnit = pageCount === 1 && pageCountUnit.endsWith('s')
    ? pageCountUnit.slice(0, -1)
    : pageCountUnit;

  return (
    <div className="flex-shrink-0 px-3 py-2 border-t border-slate-700 bg-slate-800/50">
      <div className="flex items-center justify-between gap-2 text-xs">
        {/* Left: Page count */}
        {pageCount !== undefined && (
          <div className="text-slate-400">
            {pageCount} {displayUnit} {pageCountSuffix}
          </div>
        )}

        {/* Right: Status */}
        {status && (
          <div className="text-slate-300 font-medium">
            {status}
          </div>
        )}

        {/* Optional children */}
        {children}
      </div>
    </div>
  );
}
