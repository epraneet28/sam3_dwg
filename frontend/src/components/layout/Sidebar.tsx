/**
 * Main navigation sidebar
 * Based on docling-interactive pattern, adapted for SAM3
 */

import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import {
  Squares2X2Icon,
  MagnifyingGlassIcon,
  SparklesIcon,
  Cog6ToothIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline';
import { useStore, useDocuments, useSidebarCollapsed } from '../../store';
import {
  SidebarHeader,
  SidebarBody,
  SidebarSection,
  SidebarHeading,
  SidebarDivider,
  SidebarItem,
  SidebarFooter,
} from './sidebar/compounds';

export default function Sidebar() {
  const collapsed = useSidebarCollapsed();
  const toggleSidebar = useStore((state) => state.toggleSidebar);
  const documents = useDocuments();

  const hasDocuments = documents.length > 0;
  // Navigate to most recent document (first in list, sorted by uploadedAt desc)
  const viewerPath = hasDocuments ? `/viewer/${documents[0].id}` : '/viewer';

  return (
    <div className="flex h-screen flex-col bg-zinc-900">
      {/* Header with logo and collapse toggle */}
      <SidebarHeader>
        {!collapsed && (
          <div className="flex items-center gap-3">
            {/* Logo */}
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600">
              <MagnifyingGlassIcon className="h-6 w-6 text-white" />
            </div>

            {/* Brand */}
            <div className="min-w-0 flex-1">
              <h1 className="truncate text-base font-semibold text-white">
                SAM3 Segmenter
              </h1>
              <p className="truncate text-xs text-zinc-500">
                Drawing Zone Analysis
              </p>
            </div>
          </div>
        )}

        {/* Collapse toggle */}
        <button
          onClick={toggleSidebar}
          className="absolute right-2 top-4 rounded-lg p-1.5 text-zinc-400 hover:bg-white/5 hover:text-white transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRightIcon className="h-5 w-5" />
          ) : (
            <ChevronLeftIcon className="h-5 w-5" />
          )}
        </button>
      </SidebarHeader>

      {/* Navigation content */}
      <SidebarBody>
        {/* Main Navigation */}
        <SidebarSection>
          <SidebarHeading collapsed={collapsed}>Navigation</SidebarHeading>

          <SidebarItem
            to="/"
            icon={Squares2X2Icon}
            collapsed={collapsed}
          >
            Dashboard
          </SidebarItem>

          <SidebarItem
            to={viewerPath}
            icon={MagnifyingGlassIcon}
            disabled={!hasDocuments}
            unlockHint="Upload a drawing first"
            collapsed={collapsed}
          >
            Viewer
          </SidebarItem>

          <SidebarItem
            to="/playground"
            icon={BeakerIcon}
            disabled={!hasDocuments}
            unlockHint="Upload a drawing first"
            collapsed={collapsed}
          >
            Playground
          </SidebarItem>

          <SidebarItem
            to="/exemplars"
            icon={SparklesIcon}
            disabled={true}
            unlockHint="Coming soon"
            collapsed={collapsed}
          >
            Exemplar Management
          </SidebarItem>
        </SidebarSection>

        <SidebarDivider />

        {/* Settings */}
        <SidebarSection>
          <SidebarItem
            to="/settings"
            icon={Cog6ToothIcon}
            collapsed={collapsed}
          >
            Settings
          </SidebarItem>
        </SidebarSection>

        {/* Spacer for footer at bottom */}
        <div className="flex-1" />
      </SidebarBody>

      {/* Footer with document count */}
      <SidebarFooter>
        <div className="flex justify-center rounded-lg bg-white/5 px-3 py-2 text-xs text-zinc-400">
          {collapsed ? documents.length : `${documents.length} drawings`}
        </div>
      </SidebarFooter>
    </div>
  );
}
