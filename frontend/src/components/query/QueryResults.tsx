import React from 'react';
import { motion } from 'framer-motion';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import {
  Clock,
  MapPin,
  Shield,
  AlertTriangle,
  Eye,
  Download,
} from 'lucide-react';
import { LogEvent } from '../../types';
import { DateUtils, SeverityColors } from '../../services/utils';
import { apiService } from '../../services/api';

interface QueryResultsProps {
  events: LogEvent[];
  loading: boolean;
  queryTime?: number;
  totalCount?: number;
  aiInsights?: string;
}

const QueryResults: React.FC<QueryResultsProps> = ({
  events,
  loading,
  queryTime,
  totalCount,
  aiInsights,
}) => {
  const getSeverityColor = (severity: string) => {
    return SeverityColors[severity as keyof typeof SeverityColors] || SeverityColors.low;
  };

  const handleExport = async () => {
    try {
      // Analyze the events data to create meaningful visualizations
      const analyzedData = analyzeEventsData(events);
      
      const exportData = {
        title: 'SIEM Query Results Export',
        type: 'query_results',
        include_dashboard: false,
        sections: ['query_results', 'analysis_charts', 'data_tables'],
        data: {
          events,
          queryTime,
          totalCount,
          aiInsights,
          exportDate: new Date().toISOString(),
          analysis: analyzedData
        }
      };

      const response = await apiService.exportToPDF(exportData);
      
      // Create blob and download
      const blob = new Blob([response], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `siem-query-results-${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
      // Fallback: export as JSON with analysis
      const analyzedData = analyzeEventsData(events);
      const exportData = {
        events,
        queryTime,
        totalCount,
        aiInsights,
        analysis: analyzedData,
        exportDate: new Date().toISOString()
      };
      const jsonData = JSON.stringify(exportData, null, 2);
      const blob = new Blob([jsonData], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `siem-query-results-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }
  };

  // Analyze events data to create visualizations
  const analyzeEventsData = (events: LogEvent[]) => {
    const analysis = {
      severityDistribution: {} as Record<string, number>,
      sourceIpCounts: {} as Record<string, number>,
      ruleDistribution: {} as Record<string, number>,
      timelineData: [] as Array<{hour: string, count: number}>,
      topAlerts: [] as Array<{rule: string, count: number}>,
      geoDistribution: {} as Record<string, number>
    };

    // Analyze severity distribution
    events.forEach(event => {
      const severity = event.severity || 'unknown';
      analysis.severityDistribution[severity] = (analysis.severityDistribution[severity] || 0) + 1;
      
      // Analyze source IPs
      const sourceIp = event.source_ip || 'unknown';
      analysis.sourceIpCounts[sourceIp] = (analysis.sourceIpCounts[sourceIp] || 0) + 1;
      
      // Analyze rules
      const ruleName = event.event_type || event.description || 'unknown';
      analysis.ruleDistribution[ruleName] = (analysis.ruleDistribution[ruleName] || 0) + 1;
      
      // Analyze geography (simplified)
      let country = 'unknown';
      if (sourceIp.startsWith('192.168.') || sourceIp.startsWith('10.') || sourceIp.startsWith('172.16.')) {
        country = 'Internal Network';
      } else if (sourceIp.startsWith('203.0.113.')) {
        country = 'Russia';
      } else if (sourceIp.startsWith('198.51.100.')) {
        country = 'United Kingdom';
      } else if (sourceIp.startsWith('169.254.')) {
        country = 'China';
      }
      analysis.geoDistribution[country] = (analysis.geoDistribution[country] || 0) + 1;
    });

    // Create timeline data (24-hour buckets)
    const hourCounts: Record<string, number> = {};
    events.forEach(event => {
      try {
        const timestamp = event.timestamp || new Date().toISOString();
        const hour = new Date(timestamp).getHours();
        const hourKey = `${hour.toString().padStart(2, '0')}:00`;
        hourCounts[hourKey] = (hourCounts[hourKey] || 0) + 1;
      } catch (e) {
        // Skip invalid timestamps
      }
    });

    for (let i = 0; i < 24; i++) {
      const hourKey = `${i.toString().padStart(2, '0')}:00`;
      analysis.timelineData.push({
        hour: hourKey,
        count: hourCounts[hourKey] || 0
      });
    }

    // Get top alerts
    analysis.topAlerts = Object.entries(analysis.ruleDistribution)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10)
      .map(([rule, count]) => ({ rule, count }));

    return analysis;
  };

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-4"
      >
        <Card className="p-6">
          <div className="flex items-center justify-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-neon-blue"></div>
            <span className="text-muted-foreground">Analyzing security events...</span>
          </div>
        </Card>
      </motion.div>
    );
  }

  if (events.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card className="p-8 text-center">
          <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">
            No Events Found
          </h3>
          <p className="text-muted-foreground">
            Try adjusting your query or expanding the time range.
          </p>
        </Card>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      {/* Query Summary */}
      <Card className="bg-card/50 backdrop-blur-sm">
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-neon-blue" />
                <span className="text-sm text-muted-foreground">
                  Query executed in {queryTime}ms
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <Shield className="h-4 w-4 text-neon-green" />
                <span className="text-sm text-muted-foreground">
                  Found {totalCount || (events ? events.length : 0)} events
                </span>
              </div>
            </div>
            <div className="flex space-x-2">
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          {/* AI Insights */}
          {aiInsights && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-500/30 rounded-lg p-4"
            >
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-purple-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-purple-300 mb-1">
                    AI Analysis
                  </h4>
                  <p className="text-sm text-foreground leading-relaxed">
                    {aiInsights}
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </Card>

      {/* Results Table */}
      <Card className="bg-card/50 backdrop-blur-sm">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-border/50">
                <TableHead className="w-[140px]">Timestamp</TableHead>
                <TableHead className="w-[120px]">Source IP</TableHead>
                <TableHead className="w-[100px]">Severity</TableHead>
                <TableHead className="w-[150px]">Event Type</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="w-[100px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {events && events.map((event, index) => (
                <motion.tr
                  key={event.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="border-border/50 hover:bg-accent/20 transition-colors"
                >
                  <TableCell className="font-mono text-xs">
                    <div className="flex items-center space-x-2">
                      <Clock className="h-3 w-3 text-muted-foreground" />
                      <span>{DateUtils.formatTimestamp(event.timestamp)}</span>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono">
                    <div className="flex items-center space-x-2">
                      <MapPin className="h-3 w-3 text-muted-foreground" />
                      <span>{event.source_ip}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={`${getSeverityColor(event.severity).bg} ${getSeverityColor(event.severity).text} text-xs`}
                    >
                      {event.severity}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm font-medium">
                      {event.event_type}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="max-w-md">
                      <p className="text-sm text-foreground truncate">
                        {event.description}
                      </p>
                      {event.tags && event.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {event.tags.slice(0, 3).map((tag) => (
                            <Badge
                              key={tag}
                              variant="secondary"
                              className="text-xs"
                            >
                              {tag}
                            </Badge>
                          ))}
                          {event.tags.length > 3 && (
                            <Badge variant="secondary" className="text-xs">
                              +{event.tags.length - 3}
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </motion.tr>
              ))}
            </TableBody>
          </Table>
        </div>
      </Card>
    </motion.div>
  );
};

export default QueryResults;