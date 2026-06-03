/** Tipos para el dashboard. */

export interface DashboardSummary {
  total_gastado: number;
  total_ingresos: number;
  promedio_diario: number;
  pct_cupo_utilizado: number;
  dias_para_corte: number;
  variacion_vs_anterior: number;
  score_salud_financiera?: number;
}

export interface CategoryBreakdown {
  items: Array<{
    categoria: string;
    total: number;
    percentage: number;
    color: string;
  }>;
  otros: {
    total: number;
    percentage: number;
  };
}

export interface DailyExpense {
  items: Array<{
    dia: string;
    total: number;
    categorias: Record<string, number>;
  }>;
  promedio: number;
}

export interface MonthlyTrend {
  items: Array<{
    mes: string;
    gastos: number;
    ingresos: number;
    saldo_neto: number;
  }>;
  promedio_movil: number;
}
