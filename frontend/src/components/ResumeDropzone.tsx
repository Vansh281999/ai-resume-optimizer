import { Upload } from 'lucide-react';
import { useState } from 'react';

export function ResumeDropzone({ onFile, title, description, accepted, disabled = false, loading = false }: { onFile: (file: File) => void; title: string; description: string; accepted: string; disabled?: boolean; loading?: boolean }) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFile = (file: File | undefined) => {
    if (!file || disabled || loading) return;
    setSelectedFile(file);
    onFile(file);
  };

  return (
    <label
      className={`glass-card flex cursor-pointer flex-col items-center gap-3 py-8 transition ${dragActive ? 'border-primary-400 bg-primary-50 dark:bg-primary-950/20' : ''} ${disabled || loading ? 'opacity-60' : ''}`}
      onDragOver={(event) => { event.preventDefault(); event.stopPropagation(); if (!disabled && !loading) setDragActive(true); }}
      onDragLeave={(event) => { event.preventDefault(); event.stopPropagation(); setDragActive(false); }}
      onDrop={(event) => { event.preventDefault(); event.stopPropagation(); setDragActive(false); handleFile(event.dataTransfer.files?.[0]); }}
    >
      <Upload className="size-8 text-primary-600" />
      <span className="font-semibold">{loading ? 'Processing...' : title}</span>
      <span className="text-xs text-slate-500">{description}</span>
      {selectedFile && <span className="text-xs text-slate-600 dark:text-slate-300">{selectedFile.name} • {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>}
      {loading && <span className="h-1 w-48 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"><span className="block h-full w-1/2 animate-pulse rounded-full bg-primary-500" /></span>}
      <input type="file" accept={accepted} className="hidden" disabled={disabled || loading} onChange={(event) => handleFile(event.target.files?.[0])} />
    </label>
  );
}
