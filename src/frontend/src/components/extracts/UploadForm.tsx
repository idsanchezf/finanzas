'use client';

import { useState, useCallback } from 'react';
import { Card } from '@/components/ui/Card';
import { api } from '@/lib/api';

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith('.xlsx')) {
      setFile(droppedFile);
      setError(null);
    } else {
      setError('Solo se aceptan archivos Excel (.xlsx)');
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      // TODO: Add tarjeta_id from user context
      const result = await api.upload('/extracts/upload?tarjeta_id=demo', formData);
      console.log('Upload success:', result);
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al subir el archivo');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-lg font-semibold text-gray-900">Cargar nuevo extracto</h2>
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 p-8 transition-colors hover:border-primary-400"
      >
        <span className="mb-2 text-4xl">📤</span>
        <p className="mb-1 text-sm font-medium text-gray-700">
          Arrastra tu extracto aqui o haz clic para seleccionar
        </p>
        <p className="mb-4 text-xs text-gray-500">
          Formatos aceptados: .xlsx (Excel). Maximo 10MB.
        </p>
        <input
          type="file"
          accept=".xlsx,.xls"
          onChange={handleFileChange}
          className="hidden"
          id="file-upload"
        />
        <label htmlFor="file-upload" className="btn-secondary cursor-pointer text-sm">
          Seleccionar archivo
        </label>
      </div>

      {file && (
        <div className="mt-4 flex items-center justify-between rounded-lg bg-primary-50 p-3">
          <div className="flex items-center gap-3">
            <span className="text-xl">📊</span>
            <div>
              <p className="text-sm font-medium text-primary-800">{file.name}</p>
              <p className="text-xs text-primary-600">{(file.size / 1024).toFixed(0)} KB</p>
            </div>
          </div>
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="btn-primary text-sm"
          >
            {uploading ? 'Subiendo...' : 'Procesar'}
          </button>
        </div>
      )}

      {error && (
        <div className="mt-3 rounded-lg bg-danger-50 p-3 text-sm text-danger-700">
          {error}
        </div>
      )}
    </Card>
  );
}
