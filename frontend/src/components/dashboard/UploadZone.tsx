import { useState, useRef } from 'react';
import { ArrowUpTrayIcon } from '@heroicons/react/24/outline';

interface UploadZoneProps {
  onUpload: (file: File) => void;
  uploading?: boolean;
}

export function UploadZone({ onUpload, uploading = false }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      validateAndUpload(file);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndUpload(file);
    }
  };

  const validateAndUpload = (file: File) => {
    // Clear any previous errors
    setValidationError(null);

    // Validate file type
    const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      setValidationError('Please upload a PDF or image file (PNG, JPEG)');
      return;
    }

    // Validate file size (50MB max)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      setValidationError('File size must be less than 50MB');
      return;
    }

    onUpload(file);
  };

  return (
    <>
      {validationError && (
        <div className="mb-3 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
          {validationError}
        </div>
      )}
      <div
        className={`
          border-2 border-dashed rounded-lg p-12 text-center
          transition-colors cursor-pointer
          ${isDragging
            ? 'border-blue-400 bg-blue-500/10'
            : 'border-slate-600 hover:border-slate-500 bg-slate-800/50'
          }
          ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
      >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        onChange={handleFileSelect}
        className="hidden"
        disabled={uploading}
      />

      <ArrowUpTrayIcon className="mx-auto h-12 w-12 text-slate-400 mb-4" />

      {uploading ? (
        <>
          <p className="text-lg font-medium text-white mb-2">Uploading...</p>
          <p className="text-sm text-slate-400">Please wait while we process your document</p>
          <div className="mt-4 w-full max-w-xs mx-auto bg-slate-700 rounded-full h-2">
            <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
          </div>
        </>
      ) : (
        <>
          <p className="text-lg font-medium text-white mb-2">
            Drop your drawing here or click to browse
          </p>
          <p className="text-sm text-slate-400">
            PDF, PNG, or JPEG up to 50MB
          </p>
        </>
      )}
      </div>
    </>
  );
}
