/** Cliente de API para endpoints de dashboard. */

import { api } from '@/lib/api';
import type {
  DashboardSummary,
  CategoryBreakdown,
  DailyExpense,
  MonthlyTrend,
} from '@/types/dashboard';

export interface DashboardParams {
  card_id?: string;
  period: string; // YYYY-MM
}

export const dashboardApi = {
  getSummary(params: DashboardParams): Promise<DashboardSummary> {
    return api.get<DashboardSummary>('/dashboards/summary', { card_id: params.card_id, period: params.period });
  },

  getByCategory(params: DashboardParams): Promise<CategoryBreakdown> {
    return api.get<CategoryBreakdown>('/dashboards/by-category', { card_id: params.card_id, period: params.period });
  },

  getDaily(params: DashboardParams): Promise<DailyExpense> {
    return api.get<DailyExpense>('/dashboards/daily', { card_id: params.card_id, period: params.period });
  },

  getMonthlyTrend(params: DashboardParams): Promise<MonthlyTrend> {
    return api.get<MonthlyTrend>('/dashboards/monthly-trend', { card_id: params.card_id, period: params.period });
  },

  /** Carga todos los datos del dashboard en paralelo. */
  async getAll(params: DashboardParams): Promise<DashboardAllData> {
    const [summary, byCategory, daily, monthlyTrend] = await Promise.all([
      this.getSummary(params),
      this.getByCategory(params),
      this.getDaily(params),
      this.getMonthlyTrend(params),
    ]);
    return { summary, byCategory, daily, monthlyTrend };
  },
};

export interface DashboardAllData {
  summary: DashboardSummary;
  byCategory: CategoryBreakdown;
  daily: DailyExpense;
  monthlyTrend: MonthlyTrend;
}
