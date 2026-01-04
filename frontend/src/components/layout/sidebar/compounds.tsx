/**
 * Reusable sidebar compound components
 * Based on docling-interactive pattern
 */

import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LockClosedIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

/**
 * SidebarHeader - Top section with logo and collapse toggle
 */
export function SidebarHeader({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex flex-col border-b border-white/5 p-4">
      {children}
    </div>
  );
}

/**
 * SidebarBody - Scrollable content area
 */
export function SidebarBody({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-1 flex-col overflow-y-auto p-4">
      {children}
    </div>
  );
}

/**
 * SidebarSection - Group of navigation items
 */
export function SidebarSection({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      {children}
    </div>
  );
}

/**
 * SidebarHeading - Section title
 */
export function SidebarHeading({ children, collapsed }: { children: ReactNode; collapsed?: boolean }) {
  if (collapsed) return null;

  return (
    <h3 className="mb-2 px-2 text-xs font-medium uppercase tracking-wider text-zinc-500">
      {children}
    </h3>
  );
}

/**
 * SidebarDivider - Separator between sections
 */
export function SidebarDivider() {
  return <div className="my-4 border-t border-white/5" />;
}

/**
 * SidebarItem - Navigation link
 */
interface SidebarItemProps {
  to: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  children: ReactNode;
  badge?: number;
  disabled?: boolean;
  unlockHint?: string;
  collapsed?: boolean;
}

export function SidebarItem({
  to,
  icon: Icon,
  children,
  badge,
  disabled = false,
  unlockHint,
  collapsed = false,
}: SidebarItemProps) {
  const location = useLocation();
  const isActive = location.pathname === to || location.pathname.startsWith(to + '/');

  const baseClasses = clsx(
    'relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all',
    'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-zinc-900',
    {
      // Active state (no background, just left border accent)
      'text-white': isActive && !disabled,
      'before:absolute before:-left-4 before:top-1/2 before:h-6 before:w-0.5 before:-translate-y-1/2 before:rounded-full before:bg-white':
        isActive && !disabled && !collapsed,

      // Inactive/default state
      'text-zinc-400 hover:text-white hover:bg-white/5': !isActive && !disabled,

      // Disabled state
      'cursor-not-allowed text-zinc-600': disabled,

      // Collapsed mode
      'justify-center': collapsed,
    }
  );

  const content = (
    <>
      <Icon className={clsx('h-5 w-5 flex-shrink-0', {
        'text-white': isActive && !disabled,
        'text-zinc-500': !isActive && !disabled,
        'text-zinc-600': disabled,
      })} />

      {!collapsed && (
        <>
          <span className="flex-1 truncate">{children}</span>

          {/* Badge count */}
          {!disabled && badge !== undefined && badge > 0 && (
            <span className="flex-shrink-0 rounded-full bg-white/10 px-2 py-0.5 text-xs">
              {badge}
            </span>
          )}

          {/* Lock icon for disabled items */}
          {disabled && <LockClosedIcon className="h-4 w-4 text-zinc-600" />}
        </>
      )}

      {/* Badge dot in collapsed mode */}
      {collapsed && !disabled && badge !== undefined && badge > 0 && (
        <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-blue-500" />
      )}
    </>
  );

  if (disabled) {
    return (
      <div className={baseClasses} title={unlockHint || 'Not available'}>
        {content}
      </div>
    );
  }

  return (
    <Link to={to} className={baseClasses}>
      {content}
    </Link>
  );
}

/**
 * SidebarFooter - Bottom section (e.g., document count)
 */
export function SidebarFooter({ children }: { children: ReactNode }) {
  return (
    <div className="border-t border-white/5 p-2">
      {children}
    </div>
  );
}
