import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  LoginRequest,
  LoginResponse,
  QueryRequest,
  QueryResponse,
  DashboardMetrics,
  HealthStatus,
  ReportRequest,
  ReportResponse,
  SuggestionResponse,
  UserSettings,
  PaginatedResponse,
  PaginationParams,
} from '../types';

class ApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    // Default to backend server, can be configured
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user_data');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response: AxiosResponse<LoginResponse> = await this.api.post('/auth/login', credentials);
      
      // Store token and user data
      localStorage.setItem('auth_token', response.data.access_token);
      localStorage.setItem('user_data', JSON.stringify(response.data.user));
      
      return response.data;
    } catch (error) {
      console.error('Login failed:', error);
      throw new Error('Invalid credentials');
    }
  }

  async logout(): Promise<void> {
    try {
      await this.api.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
    }
  }

  // Dashboard
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    try {
      const response = await this.api.get('/dashboard');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch dashboard metrics:', error);
      // Return mock data if backend is unavailable
      return this.getMockDashboardMetrics();
    }
  }

  // Query Console
  async queryLogs(queryRequest: QueryRequest): Promise<QueryResponse> {
    try {
      const response = await this.api.post('/query', queryRequest);
      const backendResponse = response.data;
      
      // Transform backend LogResult to frontend LogEvent format
      const transformedResults = backendResponse.results?.map((result: any) => ({
        id: result.event_id || `${Date.now()}-${Math.random()}`,
        timestamp: result.timestamp,
        source_ip: result.source_ip || 'Unknown',
        destination_ip: result.destination_ip,
        user: result.user,
        event_type: result.rule_description || 'Security Event',
        severity: result.severity || 'medium',
        description: result.details || result.rule_description || 'Security event detected',
        raw_log: JSON.stringify(result.raw_data || {}),
        tags: result.rule_id ? [result.rule_id] : [],
        status: 'new' as const,
        location: undefined // We can add geolocation logic later
      })) || [];

      return {
        summary: backendResponse.summary,
        results: transformedResults,
        query_stats: backendResponse.query_stats,
        session_id: backendResponse.session_id,
        suggestions: backendResponse.suggestions,
        has_more_results: backendResponse.has_more_results
      };
    } catch (error) {
      console.error('Query failed:', error);
      throw new Error('Failed to execute query');
    }
  }

  async getSuggestions(): Promise<SuggestionResponse> {
    try {
      const response = await this.api.get('/suggestions');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
      return {
        suggestions: [
          'Show failed logins in last 24 hours',
          'Find suspicious network traffic',
          'List critical security alerts',
          'Show login attempts from foreign IPs',
          'Find malware detections this week',
          'Show privilege escalation attempts',
          'List blocked network connections',
          'Find unusual user activity',
        ],
        categories: [
          {
            name: 'Authentication',
            suggestions: ['Show failed logins', 'List successful logins', 'Find brute force attacks'],
          },
          {
            name: 'Network',
            suggestions: ['Show network anomalies', 'List blocked connections', 'Find port scans'],
          },
          {
            name: 'Malware',
            suggestions: ['Find malware detections', 'Show virus alerts', 'List quarantined files'],
          },
        ]
      };
    }
  }

  // Reports
  async generateReport(reportRequest: ReportRequest): Promise<ReportResponse> {
    try {
      const response = await this.api.post('/reports/generate', reportRequest);
      return response.data;
    } catch (error) {
      console.error('Report generation failed:', error);
      throw new Error('Failed to generate report');
    }
  }

  async getReports(params?: PaginationParams): Promise<PaginatedResponse<ReportResponse>> {
    try {
      const response = await this.api.get('/reports', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch reports:', error);
      throw new Error('Failed to fetch reports');
    }
  }

  // Health Monitoring
  async getHealthStatus(): Promise<HealthStatus> {
    try {
      const response = await this.api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch health status:', error);
      return this.getMockHealthStatus();
    }
  }

  // Settings
  async getUserSettings(): Promise<UserSettings> {
    try {
      const response = await this.api.get('/settings/user');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch user settings:', error);
      return this.getMockUserSettings();
    }
  }

  async updateUserSettings(settings: Partial<UserSettings>): Promise<UserSettings> {
    try {
      const response = await this.api.put('/settings/user', settings);
      return response.data;
    } catch (error) {
      console.error('Failed to update user settings:', error);
      throw new Error('Failed to update settings');
    }
  }

  // Test connection
  async testConnection(): Promise<boolean> {
    try {
      const response = await this.api.get('/health');
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  // Mock data methods for demo purposes
  private getMockDashboardMetrics(): DashboardMetrics {
    return {
      total_events: 15847,
      alerts_24h: 42,
      failed_logins: 127,
      critical_threats: 8,
      system_uptime: '15d 6h 23m',
      top_source_ips: [
        { ip: '192.168.1.100', count: 234, country: 'United States', threat_level: 'high' },
        { ip: '10.0.0.45', count: 189, country: 'Germany', threat_level: 'medium' },
        { ip: '172.16.0.23', count: 156, country: 'China', threat_level: 'critical' },
        { ip: '203.0.113.42', count: 134, country: 'Russia', threat_level: 'high' },
        { ip: '198.51.100.15', count: 98, country: 'United Kingdom', threat_level: 'low' },
      ],
      events_per_hour: Array.from({ length: 24 }, (_, i) => ({
        hour: `${i.toString().padStart(2, '0')}:00`,
        count: Math.floor(Math.random() * 100) + 50,
      })),
      severity_distribution: [
        { severity: 'Low', count: 8945, percentage: 56.4 },
        { severity: 'Medium', count: 4231, percentage: 26.7 },
        { severity: 'High', count: 2134, percentage: 13.5 },
        { severity: 'Critical', count: 537, percentage: 3.4 },
      ],
      threat_timeline: [
        { time: '09:00', event_type: 'Failed Login', count: 23, severity: 'medium' },
        { time: '10:30', event_type: 'Malware Detection', count: 5, severity: 'critical' },
        { time: '11:15', event_type: 'Suspicious Network Activity', count: 12, severity: 'high' },
        { time: '14:22', event_type: 'Privilege Escalation', count: 3, severity: 'critical' },
        { time: '16:45', event_type: 'Data Exfiltration Attempt', count: 7, severity: 'high' },
      ],
    };
  }

  private getMockSuggestions(): SuggestionResponse {
    return {
      suggestions: [
        'Show failed logins in last 24 hours',
        'Find suspicious network traffic',
        'List critical security alerts',
        'Show login attempts from foreign IPs',
        'Find malware detections this week',
        'Show privilege escalation attempts',
        'List blocked network connections',
        'Find unusual user activity',
      ],
      categories: [
        {
          name: 'Authentication',
          icon: 'shield',
          suggestions: [
            'Show failed logins',
            'Find brute force attacks',
            'List successful logins from new locations',
            'Show password policy violations',
          ],
        },
        {
          name: 'Network Security',
          icon: 'network',
          suggestions: [
            'Find suspicious network traffic',
            'Show blocked connections',
            'List port scan attempts',
            'Find DNS anomalies',
          ],
        },
        {
          name: 'Malware',
          icon: 'bug',
          suggestions: [
            'Show malware detections',
            'Find quarantined files',
            'List virus scan results',
            'Show suspicious file downloads',
          ],
        },
      ],
    };
  }

  private getMockHealthStatus(): HealthStatus {
    return {
      status: 'healthy',
      uptime: '15d 6h 23m',
      version: '1.0.0',
      last_updated: new Date().toISOString(),
      services: [
        {
          name: 'Elasticsearch',
          status: 'online',
          response_time_ms: 45,
          last_check: new Date().toISOString(),
          endpoint: 'http://localhost:9200',
        },
        {
          name: 'AI Query Engine',
          status: 'online',
          response_time_ms: 120,
          last_check: new Date().toISOString(),
        },
        {
          name: 'Log Ingestion',
          status: 'online',
          response_time_ms: 23,
          last_check: new Date().toISOString(),
        },
        {
          name: 'Alert System',
          status: 'online',
          response_time_ms: 67,
          last_check: new Date().toISOString(),
        },
      ],
      performance: {
        cpu_usage: 34.5,
        memory_usage: 67.2,
        disk_usage: 42.8,
        network_io: {
          bytes_sent: 1024768,
          bytes_received: 2048576,
        },
        active_connections: 47,
        queries_per_minute: 156,
      },
    };
  }

  private getMockUserSettings(): UserSettings {
    return {
      user_profile: {
        username: 'security_analyst',
        email: 'analyst@company.com',
        role: 'Senior Security Analyst',
        timezone: 'UTC',
      },
      preferences: {
        theme: 'dark',
        language: 'en',
        dashboard_refresh_rate: 30,
        notifications: {
          email_alerts: true,
          browser_notifications: true,
          critical_alerts_only: false,
          daily_summary: true,
        },
      },
      api_settings: {
        backend_url: this.baseURL,
        timeout_seconds: 30,
        max_results_per_page: 100,
      },
    };
  }

  // Utility methods
  getCurrentUser() {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth_token');
  }

  setBaseURL(url: string) {
    this.baseURL = url;
    this.api.defaults.baseURL = url;
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;