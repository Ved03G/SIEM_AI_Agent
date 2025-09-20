import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Shield, 
  AlertTriangle, 
  Users, 
  Lock,
  Activity,
  TrendingUp,
  Clock,
  Globe
} from 'lucide-react';
import MetricCard from '../components/dashboard/MetricCard';
import TopIPsCard from '../components/dashboard/TopIPsCard';
import QuickChart from '../components/dashboard/QuickChart';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { DashboardMetrics } from '../types';
import { apiService } from '../services/api';
import { DateUtils, FormatUtils } from '../services/utils';

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const data = await apiService.getDashboardMetrics();
        setMetrics(data);
        setLastUpdated(new Date().toISOString());
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setLoading(true);
    window.location.reload();
  };

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-neon-blue"></div>
          <span className="text-lg text-muted-foreground">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Unable to load dashboard
          </h3>
          <p className="text-muted-foreground mb-4">
            There was an error loading the dashboard data.
          </p>
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
          <h1 className="text-3xl font-bold text-foreground">
            Security Dashboard
          </h1>
          <p className="text-muted-foreground">
            Real-time security intelligence and threat monitoring
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Last updated</div>
            <div className="text-sm font-medium text-foreground">
              {DateUtils.formatRelativeTime(lastUpdated)}
            </div>
          </div>
          <Button 
            onClick={handleRefresh} 
            variant="outline" 
            size="sm"
            disabled={loading}
          >
            <Activity className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </motion.div>

      {/* System Status Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="bg-gradient-to-r from-green-900/20 to-green-800/20 border-green-500/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-400 font-medium">System Operational</span>
                <Badge variant="secondary" className="bg-green-900/50 text-green-300">
                  Uptime: {metrics.system_uptime}
                </Badge>
              </div>
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <span>🛡️ AI Detection: Active</span>
                <span>📊 Log Ingestion: {FormatUtils.formatNumber(2340)}/min</span>
                <span>⚡ Response Time: 23ms</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Events"
          value={metrics.total_events}
          icon={Shield}
          trend={{ value: 12.5, label: 'from yesterday' }}
          status="neutral"
          delay={0.1}
        />
        <MetricCard
          title="Active Alerts"
          value={metrics.alerts_24h}
          icon={AlertTriangle}
          trend={{ value: -8.2, label: 'from yesterday' }}
          status="negative"
          delay={0.2}
        />
        <MetricCard
          title="Failed Logins"
          value={metrics.failed_logins}
          icon={Lock}
          trend={{ value: 15.3, label: 'from yesterday' }}
          status="negative"
          delay={0.3}
        />
        <MetricCard
          title="Critical Threats"
          value={metrics.critical_threats}
          icon={TrendingUp}
          trend={{ value: -25.0, label: 'from yesterday' }}
          status="negative"
          delay={0.4}
        />
      </div>

      {/* Charts and Detailed Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Events Timeline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-2"
        >
          <QuickChart
            title="Events Per Hour (Last 24h)"
            data={metrics.events_per_hour}
            type="area"
            dataKey="count"
            nameKey="hour"
          />
        </motion.div>

        {/* Severity Distribution */}
        <QuickChart
          title="Threat Severity Distribution"
          data={metrics.severity_distribution}
          type="pie"
          dataKey="count"
          nameKey="severity"
        />
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Source IPs */}
        <TopIPsCard ips={metrics.top_source_ips} />

        {/* Recent Threat Timeline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card className="metric-card hover:cyber-glow transition-all duration-300">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Clock className="h-5 w-5 text-neon-blue" />
                <span>Recent Threat Activity</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {metrics.threat_timeline.map((event, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-3 rounded-lg bg-accent/10 hover:bg-accent/20 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="text-sm font-medium text-foreground">
                        {event.time}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {event.event_type}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge
                        variant={event.severity === 'critical' ? 'destructive' : 'secondary'}
                        className="text-xs"
                      >
                        {event.count} events
                      </Badge>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <Card className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border-blue-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  Quick Actions
                </h3>
                <p className="text-muted-foreground">
                  Jump to common security analysis tasks
                </p>
              </div>
              <div className="flex space-x-3">
                <Button variant="outline" size="sm">
                  <Globe className="h-4 w-4 mr-2" />
                  Investigate IPs
                </Button>
                <Button variant="outline" size="sm">
                  <Users className="h-4 w-4 mr-2" />
                  User Activity
                </Button>
                <Button size="sm" className="bg-neon-blue hover:bg-neon-blue/90">
                  <Shield className="h-4 w-4 mr-2" />
                  Run Analysis
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default Dashboard;