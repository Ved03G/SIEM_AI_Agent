// Authentication Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  created_at: string;
}

// SIEM Log Event Types
export interface LogEvent {
  id: string;
  timestamp: string;
  source_ip: string;
  destination_ip?: string;
  user?: string;
  event_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  raw_log: string;
  tags: string[];
  location?: {
    country: string;
    city: string;
    lat: number;
    lng: number;
  };
  status: 'new' | 'investigating' | 'resolved' | 'false_positive';
}

// Query Types
export interface QueryRequest {
  question: string;
  query_type?: 'investigation' | 'report' | 'contextual';
  session_id?: string;
  context?: string[];
  time_range?: string;
  max_results?: number;
}

export interface QueryFilters {
  start_date?: string;
  end_date?: string;
  severity?: string[];
  event_types?: string[];
  source_ips?: string[];
  users?: string[];
}

export interface QueryResponse {
  summary: string;
  results: LogEvent[];
  query_stats: {
    total_hits: number;
    query_time_ms: number;
    indices_searched: string[];
    dsl_query: any;
  };
  // Optional/extended fields depending on backend response
  session_id?: string;
  suggestions?: string[];
  has_more_results?: boolean;
  final_dsl?: any;
  strategy?: string;
  repro_curl?: string;
}

// Dashboard Metrics Types
export interface DashboardMetrics {
  total_events: number;
  alerts_24h: number;
  top_source_ips: TopIP[];
  failed_logins: number;
  critical_threats: number;
  system_uptime: string;
  events_per_hour: EventCount[];
  severity_distribution: SeverityCount[];
  threat_timeline: TimelineEvent[];
}

export interface TopIP {
  ip: string;
  count: number;
  country: string;
  threat_level: 'low' | 'medium' | 'high' | 'critical';
}

export interface EventCount {
  hour: string;
  count: number;
}

export interface SeverityCount {
  severity: string;
  count: number;
  percentage: number;
}

export interface TimelineEvent {
  time: string;
  event_type: string;
  count: number;
  severity: string;
}

// Health Monitoring Types
export interface HealthStatus {
  status: 'healthy' | 'warning' | 'critical';
  uptime: string;
  version: string;
  services: ServiceStatus[];
  performance: PerformanceMetrics;
  last_updated: string;
}

export interface ServiceStatus {
  name: string;
  status: 'online' | 'offline' | 'degraded';
  response_time_ms: number;
  last_check: string;
  endpoint?: string;
}

export interface PerformanceMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_io: {
    bytes_sent: number;
    bytes_received: number;
  };
  active_connections: number;
  queries_per_minute: number;
}

// Reports Types
export interface ReportRequest {
  report_type: 'authentication_failures' | 'malware_detections' | 'network_anomalies' | 'user_activity' | 'threat_intelligence';
  date_range: {
    start: string;
    end: string;
  };
  filters?: ReportFilters;
  format?: 'json' | 'csv' | 'pdf';
}

export interface ReportFilters {
  users?: string[];
  source_ips?: string[];
  severity_levels?: string[];
  event_types?: string[];
}

export interface ReportResponse {
  report_id: string;
  generated_at: string;
  data: LogEvent[];
  summary: ReportSummary;
  charts: ChartData[];
  recommendations: string[];
}

export interface ReportSummary {
  total_events: number;
  time_period: string;
  most_active_hour: string;
  top_threat_type: string;
  affected_users: number;
  unique_ips: number;
}

export interface ChartData {
  chart_type: 'bar' | 'line' | 'pie' | 'area' | 'scatter';
  title: string;
  data: any[];
  labels: string[];
  colors?: string[];
}

// Settings Types
export interface UserSettings {
  user_profile: {
    username: string;
    email: string;
    role: string;
    avatar_url?: string;
    timezone: string;
  };
  preferences: {
    theme: 'light' | 'dark' | 'auto';
    language: string;
    notifications: NotificationSettings;
    dashboard_refresh_rate: number;
  };
  api_settings: {
    backend_url: string;
    timeout_seconds: number;
    max_results_per_page: number;
  };
}

export interface NotificationSettings {
  email_alerts: boolean;
  browser_notifications: boolean;
  critical_alerts_only: boolean;
  daily_summary: boolean;
}

// API Response Wrapper
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

// Pagination Types
export interface PaginationParams {
  page: number;
  page_size: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Suggestions Types
export interface SuggestionResponse {
  suggestions: string[];
  categories: SuggestionCategory[];
}

export interface SuggestionCategory {
  name: string;
  suggestions: string[];
  icon?: string;
}

// Export/Import Types
export interface ExportRequest {
  format: 'json' | 'csv' | 'excel';
  data_type: 'events' | 'reports' | 'settings';
  filters?: QueryFilters;
  date_range?: {
    start: string;
    end: string;
  };
}

export interface ImportRequest {
  file: File;
  data_type: 'events' | 'rules' | 'settings';
  merge_strategy: 'replace' | 'append' | 'skip_duplicates';
}