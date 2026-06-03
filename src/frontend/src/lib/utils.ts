/** Utilidades compartidas del frontend. */

/** Formatea un numero como moneda COP. */
export function formatCOP(amount: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
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
