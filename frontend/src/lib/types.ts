export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface Activity {
  id: string;
  user_id: string;
  source: string;
  activity_type: string;
  duration_minutes: number;
  distance_km: number | null;
  avg_heart_rate: number | null;
  steps: number | null;
  resting_heart_rate: number | null;
  notes: string | null;
  start_time: string;
}

export interface ActivityList {
  items: Activity[];
  total: number;
  limit: number;
  offset: number;
}

export interface StreamPoint {
  elapsed_sec: number;
  heart_rate: number | null;
  pace_min_per_km: number | null;
}

export interface RawActivity {
  id: string;
  source: string;
  created_at: string | null;
  payload: unknown;
  extracted: unknown;
  has_image: boolean;
  streams: StreamPoint[];
}

export interface ActivityDetail {
  activity: Activity;
  raw: RawActivity | null;
}

export interface DailyHealthMetric {
  date: string;
  sleep_hours: number | null;
  steps: number | null;
  resting_heart_rate: number | null;
}

export interface HealthSummary {
  days: number;
  start_date: string;
  end_date: string;
  daily: DailyHealthMetric[];
  avg_sleep_hours: number | null;
  total_steps: number | null;
  avg_resting_heart_rate: number | null;
}

export interface WorkoutSubmission {
  status: string;
  raw_id: string;
}
