import clsx from 'clsx';

// ============================================================================
// Card Component - Project-specific container component
// ============================================================================
//
// DESIGN NOTE (Catalyst Compatibility):
// -------------------------------------
// This component is an intentional deviation from Catalyst. Catalyst UI Kit
// does not provide a Card component - it uses fieldset patterns instead.
//
// Our Card provides:
// 1. Dark theme styling with slate-800 background
// 2. Consistent ring border for visual separation
// 3. Optional hover state for clickable cards
// 4. Compound components (CardHeader, CardContent) following React patterns
//
// The styling (bg-slate-800/80, ring-1 ring-white/10) aligns with our dark
// theme and is consistent across all card usages in the application.
// ============================================================================

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
}

export function Card({ children, className, hover = false, onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={clsx(
        'bg-slate-800/80 rounded-xl shadow-lg p-4 ring-1 ring-white/10',
        hover && 'hover:bg-slate-700/50 hover:ring-white/20 transition-all cursor-pointer',
        className
      )}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  children: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function CardHeader({ children, action, className }: CardHeaderProps) {
  return (
    <div className={clsx('flex items-center justify-between mb-4', className)}>
      <h2 className="text-base font-semibold text-white">{children}</h2>
      {action}
    </div>
  );
}

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export function CardContent({ children, className }: CardContentProps) {
  return <div className={className}>{children}</div>;
}
