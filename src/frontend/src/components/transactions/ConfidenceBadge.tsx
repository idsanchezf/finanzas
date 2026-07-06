'use client';

import { getConfidenceLevel, formatConfidence, cn } from '@/lib/utils';

interface ConfidenceBadgeProps {
  confidence: number | null | undefined;
  className?: string;
}

/** Badge de nivel de confianza de clasificacion. */
export function ConfidenceBadge({ confidence, className }: ConfidenceBadgeProps) {
  const level = getConfidenceLevel(confidence);

  const variants: Record<string, string> = {
    alta: 'bg-success-50 text-success-700 border-success-200',
    media: 'bg-warning-50 text-warning-700 border-warning-200',
    baja: 'bg-danger-50 text-danger-700 border-danger-200',
    sin_clasificar: 'bg-gray-50 text-gray-500 border-gray-200',
  };

  const labels: Record<string, string> = {
    alta: 'Alta',
    media: 'Media',
    baja: 'Baja',
    sin_clasificar: 'Sin clasificar',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium',
        variants[level],
        className
      )}
    >
      <span
        className={cn(
          'inline-block h-1.5 w-1.5 rounded-full',
          level === 'alta' && 'bg-success-500',
          level === 'media' && 'bg-warning-500',
          level === 'baja' && 'bg-danger-500',
          level === 'sin_clasificar' && 'bg-gray-400'
        )}
      />
      {labels[level]}
      {level !== 'sin_clasificar' && (
        <span className="ml-0.5 opacity-70">{formatConfidence(confidence)}</span>
      )}
    </span>
  );
}
