export interface AnalyticsOverview {
  total_users: number;
  citizens: number;
  collectors: number;
  dealers: number;
  total_pickups: number;
  completed_pickups: number;
  pending_pickups: number;
  cancelled_pickups: number;
  total_weight_kg: number;
  completed_rate: number;
}

export interface MaterialBreakdown {
  plastic: number;
  paper: number;
  metal: number;
  glass: number;
  e_waste: number;
  organic: number;
  other: number;
}

export interface MonthlyStat {
  month: string;
  pickup_count: number;
  completed: number;
  weight: number;
}

export interface CollectorPerformance {
  collector_id: number;
  collector_name: string;
  completed_jobs: number;
  completion_rate: number;
  average_response_time: number;
}

export interface DealerPerformance {
  dealer_id: number;
  dealer_name: string;
  materials_processed: number;
  total_weight: number;
}

export interface CarbonSavings {
  estimated_co2_saved: number;
  trees_equivalent: number;
  plastic_recycled: number;
  paper_recycled: number;
}

export interface AnalyticsInsight {
  key: string;
  title: string;
  message: string;
}
