/**
 * Main layout component with sidebar + content area
 * Based on docling-interactive pattern
 */

import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useSidebarCollapsed } from '../../store';

export default function Layout() {
  const collapsed = useSidebarCollapsed();

  return (
    <div className="flex h-screen bg-zinc-950 overflow-hidden">
      {/* Sidebar with smooth collapse animation */}
      <div
        className={`h-screen flex-shrink-0 transition-all duration-300 ease-in-out ${
          collapsed ? 'w-16' : 'w-64'
        }`}
      >
        <Sidebar />
      </div>

      {/* Main content area */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
