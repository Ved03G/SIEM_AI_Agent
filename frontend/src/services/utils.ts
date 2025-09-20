// Auth utilities
export const AuthUtils = {
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('auth_token');
  },

  getToken: (): string | null => {
    return localStorage.getItem('auth_token');
  },

  getCurrentUser: () => {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
  },

  logout: (): void => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    window.location.href = '/login';
  },
};

// Date utilities
export const DateUtils = {
  formatTimestamp: (timestamp: string): string => {
    return new Date(timestamp).toLocaleString();
  },

  formatRelativeTime: (timestamp: string): string => {
    const now = new Date();
    const date = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  },

  getDateRange: (days: number): { start: string; end: string } => {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - days);

    return {
      start: start.toISOString(),
      end: end.toISOString(),
    };
  },
};

// Formatting utilities
export const FormatUtils = {
  formatNumber: (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  },

  formatBytes: (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  },

  formatPercentage: (value: number): string => {
    return `${value.toFixed(1)}%`;
  },

  truncateText: (text: string, maxLength: number): string => {
    if (text.length <= maxLength) return text;
    return `${text.substring(0, maxLength)}...`;
  },
};

// Color utilities for severity levels
export const SeverityColors = {
  low: {
    bg: 'bg-green-100 dark:bg-green-900/20',
    text: 'text-green-800 dark:text-green-400',
    border: 'border-green-300 dark:border-green-700',
    dot: 'bg-green-500',
  },
  medium: {
    bg: 'bg-yellow-100 dark:bg-yellow-900/20',
    text: 'text-yellow-800 dark:text-yellow-400',
    border: 'border-yellow-300 dark:border-yellow-700',
    dot: 'bg-yellow-500',
  },
  high: {
    bg: 'bg-orange-100 dark:bg-orange-900/20',
    text: 'text-orange-800 dark:text-orange-400',
    border: 'border-orange-300 dark:border-orange-700',
    dot: 'bg-orange-500',
  },
  critical: {
    bg: 'bg-red-100 dark:bg-red-900/20',
    text: 'text-red-800 dark:text-red-400',
    border: 'border-red-300 dark:border-red-700',
    dot: 'bg-red-500',
  },
};

// Status colors for system health
export const StatusColors = {
  online: {
    bg: 'bg-green-100 dark:bg-green-900/20',
    text: 'text-green-800 dark:text-green-400',
    dot: 'bg-green-500',
  },
  offline: {
    bg: 'bg-red-100 dark:bg-red-900/20',
    text: 'text-red-800 dark:text-red-400',
    dot: 'bg-red-500',
  },
  degraded: {
    bg: 'bg-yellow-100 dark:bg-yellow-900/20',
    text: 'text-yellow-800 dark:text-yellow-400',
    dot: 'bg-yellow-500',
  },
  healthy: {
    bg: 'bg-green-100 dark:bg-green-900/20',
    text: 'text-green-800 dark:text-green-400',
    dot: 'bg-green-500',
  },
  warning: {
    bg: 'bg-yellow-100 dark:bg-yellow-900/20',
    text: 'text-yellow-800 dark:text-yellow-400',
    dot: 'bg-yellow-500',
  },
};

// Validation utilities
export const ValidationUtils = {
  isValidEmail: (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  isValidIP: (ip: string): boolean => {
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ipRegex.test(ip);
  },

  isValidURL: (url: string): boolean => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  },
};

// Chart color palettes
export const ChartColors = {
  severity: ['#10b981', '#f59e0b', '#f97316', '#ef4444'], // green, yellow, orange, red
  cyber: ['#00d4ff', '#00ff88', '#8b5cf6', '#ff4757', '#ffa502'],
  gradient: [
    'rgba(0, 212, 255, 0.8)',
    'rgba(0, 255, 136, 0.8)',
    'rgba(139, 92, 246, 0.8)',
    'rgba(255, 71, 87, 0.8)',
    'rgba(255, 165, 2, 0.8)',
  ],
};