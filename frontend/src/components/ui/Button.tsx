import { forwardRef } from 'react';
import clsx from 'clsx';

// ============================================================================
// Button Component - Catalyst-inspired with dark theme
// ============================================================================
//
// API DESIGN NOTE (Catalyst Compatibility):
// -----------------------------------------
// This component uses a string-based `variant` prop ('solid' | 'outline' | 'plain')
// rather than Catalyst's boolean props (`outline`, `plain`). This design decision
// was made for consistency and type safety:
//
// Our API:     <Button variant="outline" color="blue" />
// Catalyst:    <Button outline color="blue" />
//
// The string-based approach provides:
// 1. Explicit, self-documenting code at call sites
// 2. Consistent pattern with `color` and `size` props (all string-based)
// 3. Full TypeScript union type safety
// 4. Avoidance of ambiguous states (what if both `outline` and `plain` are true?)
//
// If Catalyst-style boolean props are needed for a specific integration,
// create a thin wrapper component that maps the boolean API to our string API.
// ============================================================================

type ButtonVariant = 'solid' | 'outline' | 'plain';
type ButtonColor = 'blue' | 'green' | 'red' | 'amber' | 'zinc' | 'white';
type ButtonSize = 'xs' | 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  color?: ButtonColor;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  /** Makes the button full width. Use with className="sm:w-auto" for responsive modals. */
  fullWidth?: boolean;
}

// Base styles shared across all variants
const baseStyles = [
  'relative isolate inline-flex items-center justify-center gap-2 rounded-lg font-semibold',
  'transition-all duration-150',
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-900',
  'disabled:opacity-50 disabled:cursor-not-allowed',
];

// Size variants
const sizeStyles: Record<ButtonSize, string> = {
  xs: 'px-2 py-1 text-xs',
  sm: 'px-2.5 py-1.5 text-sm',
  md: 'px-3.5 py-2 text-sm',
  lg: 'px-4 py-2.5 text-base',
};

// Icon sizes
const iconSizeStyles: Record<ButtonSize, string> = {
  xs: 'h-3 w-3',
  sm: 'h-4 w-4',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
};

// ============================================================================
// COLOR SYSTEM NOTE:
// ============================================================================
// These color maps are intentionally separate from constants/colors.ts BUTTON_COLORS.
//
// - Button.tsx colors: Variant-specific styling (solid/outline/plain) with
//   hover, active, and focus states for each color + variant combination.
//   Used via: <Button variant="outline" color="blue" />
//
// - constants/colors.ts BUTTON_COLORS: Semantic Tailwind classes for direct
//   className usage on raw button elements (not using this Button component).
//   Used via: className={BUTTON_COLORS.primary.solid}
//
// The separation exists because this component needs variant-specific styling
// (outline buttons need different hover states than solid buttons), while
// BUTTON_COLORS provides semantic shortcuts for non-component button usage.
// ============================================================================

// Solid variant colors
const solidColors: Record<ButtonColor, string> = {
  blue: clsx(
    'bg-blue-600 text-white',
    'hover:bg-blue-500',
    'active:bg-blue-700',
    'focus-visible:ring-blue-500',
    'shadow-sm'
  ),
  green: clsx(
    'bg-emerald-600 text-white',
    'hover:bg-emerald-500',
    'active:bg-emerald-700',
    'focus-visible:ring-emerald-500',
    'shadow-sm'
  ),
  red: clsx(
    'bg-red-600 text-white',
    'hover:bg-red-500',
    'active:bg-red-700',
    'focus-visible:ring-red-500',
    'shadow-sm'
  ),
  amber: clsx(
    'bg-amber-500 text-amber-950',
    'hover:bg-amber-400',
    'active:bg-amber-600',
    'focus-visible:ring-amber-500',
    'shadow-sm'
  ),
  zinc: clsx(
    'bg-zinc-700 text-white',
    'hover:bg-zinc-600',
    'active:bg-zinc-800',
    'focus-visible:ring-zinc-500',
    'shadow-sm'
  ),
  white: clsx(
    'bg-white text-zinc-950',
    'hover:bg-zinc-100',
    'active:bg-zinc-200',
    'focus-visible:ring-white',
    'shadow-sm'
  ),
};

// Outline variant colors
const outlineColors: Record<ButtonColor, string> = {
  blue: clsx(
    'border border-blue-500/50 text-blue-400',
    'hover:bg-blue-500/10 hover:border-blue-500',
    'active:bg-blue-500/20',
    'focus-visible:ring-blue-500'
  ),
  green: clsx(
    'border border-emerald-500/50 text-emerald-400',
    'hover:bg-emerald-500/10 hover:border-emerald-500',
    'active:bg-emerald-500/20',
    'focus-visible:ring-emerald-500'
  ),
  red: clsx(
    'border border-red-500/50 text-red-400',
    'hover:bg-red-500/10 hover:border-red-500',
    'active:bg-red-500/20',
    'focus-visible:ring-red-500'
  ),
  amber: clsx(
    'border border-amber-500/50 text-amber-400',
    'hover:bg-amber-500/10 hover:border-amber-500',
    'active:bg-amber-500/20',
    'focus-visible:ring-amber-500'
  ),
  zinc: clsx(
    'border border-zinc-600 text-zinc-300',
    'hover:bg-white/5 hover:border-zinc-500 hover:text-white',
    'active:bg-white/10',
    'focus-visible:ring-zinc-500'
  ),
  white: clsx(
    'border border-white/20 text-white',
    'hover:bg-white/10 hover:border-white/40',
    'active:bg-white/20',
    'focus-visible:ring-white'
  ),
};

// Plain variant colors (no border, just text)
const plainColors: Record<ButtonColor, string> = {
  blue: clsx(
    'text-blue-400',
    'hover:bg-blue-500/10 hover:text-blue-300',
    'active:bg-blue-500/20',
    'focus-visible:ring-blue-500'
  ),
  green: clsx(
    'text-emerald-400',
    'hover:bg-emerald-500/10 hover:text-emerald-300',
    'active:bg-emerald-500/20',
    'focus-visible:ring-emerald-500'
  ),
  red: clsx(
    'text-red-400',
    'hover:bg-red-500/10 hover:text-red-300',
    'active:bg-red-500/20',
    'focus-visible:ring-red-500'
  ),
  amber: clsx(
    'text-amber-400',
    'hover:bg-amber-500/10 hover:text-amber-300',
    'active:bg-amber-500/20',
    'focus-visible:ring-amber-500'
  ),
  zinc: clsx(
    'text-zinc-400',
    'hover:bg-white/5 hover:text-white',
    'active:bg-white/10',
    'focus-visible:ring-zinc-500'
  ),
  white: clsx(
    'text-white',
    'hover:bg-white/10',
    'active:bg-white/20',
    'focus-visible:ring-white'
  ),
};

function getVariantStyles(variant: ButtonVariant, color: ButtonColor): string {
  switch (variant) {
    case 'solid':
      return solidColors[color];
    case 'outline':
      return outlineColors[color];
    case 'plain':
      return plainColors[color];
  }
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'solid',
      color = 'blue',
      size = 'md',
      loading = false,
      fullWidth = false,
      icon,
      iconPosition = 'left',
      className,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const iconElement = loading ? (
      <svg className={clsx('animate-spin', iconSizeStyles[size])} fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    ) : icon ? (
      <span className={clsx('shrink-0', iconSizeStyles[size])}>{icon}</span>
    ) : null;

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={clsx(
          baseStyles,
          sizeStyles[size],
          fullWidth && 'w-full',
          getVariantStyles(variant, color),
          className
        )}
        {...props}
      >
        {iconPosition === 'left' && iconElement}
        {children}
        {iconPosition === 'right' && iconElement}
      </button>
    );
  }
);

Button.displayName = 'Button';

// ============================================================================
// IconButton Component - For icon-only buttons
// ============================================================================

interface IconButtonProps extends Omit<ButtonProps, 'icon' | 'iconPosition' | 'children'> {
  icon: React.ReactNode;
  'aria-label': string;
}

const iconOnlySizeStyles: Record<ButtonSize, string> = {
  xs: 'p-1',
  sm: 'p-1.5',
  md: 'p-2',
  lg: 'p-2.5',
};

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ icon, size = 'md', variant = 'plain', color = 'zinc', className, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={clsx(
          'relative isolate inline-flex items-center justify-center rounded-lg',
          'transition-all duration-150',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-900',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          iconOnlySizeStyles[size],
          getVariantStyles(variant, color),
          className
        )}
        {...props}
      >
        <span className={iconSizeStyles[size]}>{icon}</span>
      </button>
    );
  }
);

IconButton.displayName = 'IconButton';
