import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import {
  Activity,
  Server,
  Zap,
  CheckCircle,
  AlertCircle,
  XCircle,
  RefreshCw,
  Cpu,
  MemoryStick,
  HardDrive,
  Network,
} from 'lucide-react';
import { HealthStatus } from '../types';
import { apiService } from '../services/api';
import { StatusColors, FormatUtils } from '../services/utils';

const Health: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  useEffect(() => {
    const fetchHealthData = async () => {
      try {
        setLoading(true);
        const data = await apiService.getHealthStatus();
        setHealthData(data);
        setLastUpdated(new Date().toISOString());
      } catch (error) {
        console.error('Failed to fetch health data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHealthData();

    // Auto-refresh every 15 seconds
    const interval = setInterval(fetchHealthData, 15000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'degraded':
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'offline':
      case 'critical':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Activity className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status: string) => {
    return StatusColors[status as keyof typeof StatusColors] || StatusColors.healthy;
  };

  const handleRefresh = () => {
    setLoading(true);
    window.location.reload();
  };

  if (loading && !healthData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-neon-blue"></div>
          <span className="text-lg text-muted-foreground">Loading system health...</span>
        </div>
      </div>
    );
  }

  if (!healthData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Health Data Unavailable
          </h3>
          <Button onClick={handleRefresh}>Try Again</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center space-x-3">
            <Activity className="h-8 w-8 text-neon-blue" />
            <span>System Health</span>
          </h1>
          <p className="text-muted-foreground">
            Real-time monitoring of SIEM infrastructure and services
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Last updated</div>
            <div className="text-sm font-medium text-foreground">
              {new Date(lastUpdated).toLocaleTimeString()}
            </div>
          </div>
          <Button onClick={handleRefresh} variant="outline" size="sm" disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </motion.div>

      {/* Overall Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className={`${getStatusColor(healthData.status).bg} border-2 border-green-500/30`}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                {getStatusIcon(healthData.status)}
                <div>
                  <h2 className="text-xl font-bold text-foreground">
                    System Status: {healthData.status.charAt(0).toUpperCase() + healthData.status.slice(1)}
                  </h2>
                  <p className="text-muted-foreground">
                    Uptime: {healthData.uptime} • Version: {healthData.version}
                  </p>
                </div>
              </div>
              <Badge
                className={`${getStatusColor(healthData.status).bg} ${getStatusColor(healthData.status).text} text-sm px-3 py-1`}
              >
                All Systems Operational
              </Badge>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Services Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Server className="h-5 w-5 text-neon-blue" />
                <span>Services</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {healthData.services.map((service, index) => (
                  <motion.div
                    key={service.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-3 rounded-lg bg-accent/10 hover:bg-accent/20 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(service.status)}
                      <div>
                        <div className="font-medium text-foreground">
                          {service.name}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Response: {service.response_time_ms}ms
                        </div>
                      </div>
                    </div>
                    <Badge
                      className={`${getStatusColor(service.status).bg} ${getStatusColor(service.status).text} text-xs`}
                    >
                      {service.status}
                    </Badge>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Performance Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Zap className="h-5 w-5 text-neon-blue" />
                <span>Performance</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    icon: Cpu,
                    label: 'CPU Usage',
                    value: healthData.performance.cpu_usage,
                    unit: '%',
                    max: 100,
                  },
                  {
                    icon: MemoryStick,
                    label: 'Memory Usage',
                    value: healthData.performance.memory_usage,
                    unit: '%',
                    max: 100,
                  },
                  {
                    icon: HardDrive,
                    label: 'Disk Usage',
                    value: healthData.performance.disk_usage,
                    unit: '%',
                    max: 100,
                  },
                  {
                    icon: Network,
                    label: 'Active Connections',
                    value: healthData.performance.active_connections,
                    unit: '',
                    max: 1000,
                  },
                ].map((metric, index) => {
                  const Icon = metric.icon;
                  const percentage = metric.max ? (metric.value / metric.max) * 100 : metric.value;
                  const getMetricColor = () => {
                    if (percentage < 50) return 'bg-green-500';
                    if (percentage < 80) return 'bg-yellow-500';
                    return 'bg-red-500';
                  };

                  return (
                    <motion.div
                      key={metric.label}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Icon className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm font-medium text-foreground">
                            {metric.label}
                          </span>
                        </div>
                        <span className="text-sm font-bold text-foreground">
                          {FormatUtils.formatNumber(metric.value)}{metric.unit}
                        </span>
                      </div>
                      <div className="w-full bg-accent/20 rounded-full h-2">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.min(percentage, 100)}%` }}
                          transition={{ delay: index * 0.1, duration: 0.8 }}
                          className={`h-2 rounded-full ${getMetricColor()}`}
                        />
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Network Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Network className="h-5 w-5 text-neon-blue" />
              <span>Network & Query Statistics</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[
                {
                  label: 'Bytes Sent',
                  value: FormatUtils.formatBytes(healthData.performance.network_io.bytes_sent),
                  icon: '⬆️',
                },
                {
                  label: 'Bytes Received',
                  value: FormatUtils.formatBytes(healthData.performance.network_io.bytes_received),
                  icon: '⬇️',
                },
                {
                  label: 'Queries/Minute',
                  value: healthData.performance.queries_per_minute.toString(),
                  icon: '🔍',
                },
                {
                  label: 'Active Sessions',
                  value: healthData.performance.active_connections.toString(),
                  icon: '👥',
                },
              ].map((stat, index) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className="text-center p-4 rounded-lg bg-accent/10"
                >
                  <div className="text-2xl mb-2">{stat.icon}</div>
                  <div className="text-2xl font-bold text-neon-blue mb-1">
                    {stat.value}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {stat.label}
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default Health;