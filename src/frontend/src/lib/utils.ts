/** Utilidades compartidas del frontend. */

/** Formatea un numero como moneda COP con apostrofe como separador de miles ($ 1'234.567). */
export function formatCOP(amount: number): string {
  const withDots = new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
  // Reemplaza el punto separador de miles por apostrofe: $ 1.234.567 -> $ 1'234.567
  return withDots.replace(/\.(\d{3})/g, "'$1");
}

/** Formatea un numero compacto estilo colombiano (ej. 1.2M, 350k). */
export function formatCOPCompact(amount: number): string {
  if (amount >= 1_000_000) {
    return `$${(amount / 1_000_000).toFixed(1)}M`;
  }
  if (amount >= 1_000) {
    const kValue = (amount / 1_000).toFixed(0);
    return `$${kValue.replace(/\./g, "'")}k`;
  }
  return `$${amount.toLocaleString('es-CO')}`;
}

/** Formatea un numero como porcentaje. */
export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

/** Formatea una fecha ISO a formato legible. */
export function formatDate(isoDate: string): string {
  return new Intl.DateTimeFormat('es-CO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(isoDate));
}

/** Trunca un string con ellipsis. */
export function truncate(str: string, maxLength: number = 30): string {
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength - 3) + '...';
}

/** Genera un color hex a partir de un string (consistente). */
export function stringToColor(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const color = '#' + ((hash & 0x00ffffff) | 0x1000000).toString(16).slice(1);
  return color;
}

/** Debounce para llamadas frecuentes (ej. busqueda). */
export function debounce<T extends (...args: unknown[]) => void>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

/** Clase para construir nombres de clase condicionales. */
export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}

/** Determina el nivel de confianza basado en el valor numerico. */
export function getConfidenceLevel(confidence: number | null | undefined): 'alta' | 'media' | 'baja' | 'sin_clasificar' {
  if (confidence === null || confidence === undefined) return 'sin_clasificar';
  if (confidence >= 0.8) return 'alta';
  if (confidence >= 0.5) return 'media';
  return 'baja';
}

/** Formatea el nivel de confianza para mostrar. */
export function formatConfidence(confidence: number | null | undefined): string {
  if (confidence === null || confidence === undefined) return 'Sin clasificar';
  return `${Math.round(confidence * 100)}%`;
}

/** Obtiene el color CSS para una categoria desde su valor hexadecimal. */
export function getCategoryColor(color: string, opacity?: number): string {
  if (opacity !== undefined) {
    // Convert hex to rgba
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  }
  return color;
}

/** Formatea numero de cuotas para display (ej. "3/12"). */
export function formatInstallments(actual: number | null | undefined, total: number | null | undefined): string | null {
  if (!actual && !total) return null;
  const a = actual ?? '?';
  const t = total ?? '?';
  return `${a}/${t}`;
}

/** Verifica si un valor es negativo (abono). */
export function isCredit(amount: number): boolean {
  return amount < 0;
}
