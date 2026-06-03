'use client';

import { UploadForm } from '@/components/extracts/UploadForm';
import { ExtractCard } from '@/components/extracts/ExtractCard';

export default function ExtractsPage() {
  return (
    <div className="space-y-6 p-4 md:p-6">
      <h1 className="text-2xl font-bold text-gray-900 md:text-3xl">Extractos</h1>

      <UploadForm />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <ExtractCard
          banco="Bancolombia"
          periodo="Mayo 2026"
          estado="COMPLETED"
          total={2850000}
          transacciones={67}
        />
        <ExtractCard
          banco="Bancolombia"
          periodo="Abril 2026"
          estado="COMPLETED"
          total={3120000}
          transacciones={72}
        />
      </div>
    </div>
  );
}
