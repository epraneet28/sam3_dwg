import { TrashIcon } from '@heroicons/react/24/outline';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { SAM3Document } from '../../types';

interface DocumentCardProps {
  document: SAM3Document;
  onClick: () => void;
  onDelete: (e: React.MouseEvent) => void;
}

export function DocumentCard({ document: doc, onClick, onDelete }: DocumentCardProps) {
  const totalZones = doc.pages.reduce((sum, p) => sum + p.zones.length, 0);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'segmented':
        return 'green';
      case 'pending':
        return 'amber';
      case 'error':
        return 'red';
      default:
        return 'zinc';
    }
  };

  return (
    <Card
      hover
      onClick={onClick}
      className="overflow-hidden cursor-pointer"
    >
      {/* Thumbnail */}
      <div className="h-48 bg-slate-700/50 flex items-center justify-center overflow-hidden">
        {doc.pages[0]?.imageUrl ? (
          <img
            src={doc.pages[0].imageUrl}
            alt={doc.name}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="text-slate-500 text-sm">No preview</div>
        )}
      </div>

      {/* Metadata */}
      <div className="p-4">
        <div className="font-medium text-white truncate mb-2" title={doc.name}>
          {doc.name}
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 mb-3">
          <span>{doc.totalPages} {doc.totalPages === 1 ? 'page' : 'pages'}</span>
          {totalZones > 0 && (
            <>
              <span>•</span>
              <span>{totalZones} {totalZones === 1 ? 'zone' : 'zones'}</span>
            </>
          )}
        </div>

        <div className="flex items-center justify-between">
          <Badge color={getStatusColor(doc.status)}>
            {doc.status}
          </Badge>

          {doc.error && (
            <span className="text-xs text-red-400" title={doc.error}>
              Error
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-1 p-3 border-t border-slate-700/50 bg-slate-800/30">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(e);
          }}
          className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
          title="Delete document"
        >
          <TrashIcon className="w-4 h-4" />
        </button>
      </div>
    </Card>
  );
}
