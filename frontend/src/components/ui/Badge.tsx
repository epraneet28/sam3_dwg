import clsx from 'clsx';
// import type { StageStatus } from '../../types'; // Not needed for SAM3

// ============================================================================
// Badge Component - Catalyst-inspired with dark theme
// ============================================================================

// Color palette from Catalyst
const colors = {
  // Semantic colors
  zinc: 'bg-zinc-500/10 text-zinc-400 group-hover:bg-zinc-500/20',
  blue: 'bg-blue-500/15 text-blue-400 group-hover:bg-blue-500/25',
  green: 'bg-emerald-500/15 text-emerald-400 group-hover:bg-emerald-500/25',
  emerald: 'bg-emerald-500/15 text-emerald-400 group-hover:bg-emerald-500/25',
  red: 'bg-red-500/15 text-red-400 group-hover:bg-red-500/25',
  amber: 'bg-amber-400/15 text-amber-400 group-hover:bg-amber-400/25',
  yellow: 'bg-yellow-400/15 text-yellow-300 group-hover:bg-yellow-400/25',
  orange: 'bg-orange-500/15 text-orange-400 group-hover:bg-orange-500/25',
  purple: 'bg-purple-500/15 text-purple-400 group-hover:bg-purple-500/25',
  violet: 'bg-violet-500/15 text-violet-400 group-hover:bg-violet-500/25',
  indigo: 'bg-indigo-500/15 text-indigo-400 group-hover:bg-indigo-500/25',
  pink: 'bg-pink-400/15 text-pink-400 group-hover:bg-pink-400/25',
  cyan: 'bg-cyan-400/15 text-cyan-300 group-hover:bg-cyan-400/25',
  teal: 'bg-teal-500/15 text-teal-300 group-hover:bg-teal-500/25',
  sky: 'bg-sky-500/15 text-sky-300 group-hover:bg-sky-500/25',
  lime: 'bg-lime-400/15 text-lime-300 group-hover:bg-lime-400/25',
  rose: 'bg-rose-400/15 text-rose-400 group-hover:bg-rose-400/25',
  fuchsia: 'bg-fuchsia-400/15 text-fuchsia-400 group-hover:bg-fuchsia-400/25',
};

// Dot colors
const dotColors = {
  zinc: 'bg-zinc-400',
  blue: 'bg-blue-400',
  green: 'bg-emerald-400',
  emerald: 'bg-emerald-400',
  red: 'bg-red-400',
  amber: 'bg-amber-400',
  yellow: 'bg-yellow-300',
  orange: 'bg-orange-400',
  purple: 'bg-purple-400',
  violet: 'bg-violet-400',
  indigo: 'bg-indigo-400',
  pink: 'bg-pink-400',
  cyan: 'bg-cyan-300',
  teal: 'bg-teal-300',
  sky: 'bg-sky-300',
  lime: 'bg-lime-300',
  rose: 'bg-rose-400',
  fuchsia: 'bg-fuchsia-400',
};

type BadgeColor = keyof typeof colors;
type BadgeSize = 'sm' | 'md';

interface BadgeProps {
  children: React.ReactNode;
  color?: BadgeColor;
  size?: BadgeSize;
  dot?: boolean;
  className?: string;
}

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'px-1.5 py-0.5 text-xs',
  md: 'px-2 py-0.5 text-xs',
};

export function Badge({
  children,
  color = 'zinc',
  size = 'md',
  dot = false,
  className,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        'group inline-flex items-center gap-1.5 rounded-md font-medium',
        colors[color],
        sizeStyles[size],
        className
      )}
    >
      {dot && (
        <span className={clsx('h-1.5 w-1.5 rounded-full', dotColors[color])} />
      )}
      {children}
    </span>
  );
}

// ============================================================================
// StatusBadge - For document status display
// ============================================================================

type StatusType = 'pending' | 'processing' | 'editing' | 'completed' | 'complete' | 'error' | 'failed';

const statusConfig: Record<StatusType, { color: BadgeColor; label: string }> = {
  pending: { color: 'zinc', label: 'Pending' },
  processing: { color: 'blue', label: 'Processing' },
  editing: { color: 'amber', label: 'Editing' },
  completed: { color: 'green', label: 'Completed' },
  complete: { color: 'green', label: 'Complete' },
  error: { color: 'red', label: 'Error' },
  failed: { color: 'red', label: 'Failed' },
};

export function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status as StatusType] || { color: 'zinc' as BadgeColor, label: status };

  return (
    <Badge color={config.color} dot>
      {config.label}
    </Badge>
  );
}

// ============================================================================
// StageBadge - Circular badge for pipeline stages (NOT USED IN SAM3)
// ============================================================================

/*
type StageStatus = 'pending' | 'processing' | 'current' | 'complete' | 'needs-edit' | 'error';

interface StageBadgeProps {
  status: StageStatus;
  className?: string;
}

const stageStatusStyles: Record<StageStatus, string> = {
  pending: 'bg-zinc-800 text-zinc-500 ring-zinc-700',
  processing: 'bg-blue-500/20 text-blue-400 ring-blue-500/50 animate-pulse',
  current: 'bg-blue-500/20 text-blue-400 ring-blue-500/50',
  complete: 'bg-emerald-500/20 text-emerald-400 ring-emerald-500/50',
  'needs-edit': 'bg-amber-500/20 text-amber-400 ring-amber-500/50',
  error: 'bg-red-500/20 text-red-400 ring-red-500/50',
};

const stageStatusIcons: Record<StageStatus, React.ReactNode> = {
  pending: <span className="text-xs font-medium">-</span>,
  processing: (
    <svg className="h-3 w-3 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  ),
  current: (
    <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="6" />
    </svg>
  ),
  complete: (
    <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
    </svg>
  ),
  'needs-edit': (
    <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
    </svg>
  ),
  error: (
    <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
};

export function StageBadge({ status, className }: StageBadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex h-6 w-6 items-center justify-center rounded-full ring-1 ring-inset',
        stageStatusStyles[status],
        className
      )}
    >
      {stageStatusIcons[status]}
    </span>
  );
}
*/

// ============================================================================
// CountBadge - For showing counts/numbers
// ============================================================================

interface CountBadgeProps {
  count: number;
  color?: BadgeColor;
  className?: string;
}

export function CountBadge({ count, color = 'zinc', className }: CountBadgeProps) {
  if (count === 0) return null;

  return (
    <span
      className={clsx(
        'inline-flex min-w-[1.25rem] items-center justify-center rounded-full px-1.5 py-0.5 text-xs font-medium',
        colors[color],
        className
      )}
    >
      {count > 99 ? '99+' : count}
    </span>
  );
}
