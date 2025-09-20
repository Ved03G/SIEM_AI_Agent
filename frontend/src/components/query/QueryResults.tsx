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
  Filter,
} from 'lucide-react';
import { LogEvent } from '../../types';
import { DateUtils, SeverityColors } from '../../services/utils';

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
                  Found {totalCount || events.length} events
                </span>
              </div>
            </div>
            <div className="flex space-x-2">
              <Button variant="outline" size="sm">
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </Button>
              <Button variant="outline" size="sm">
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
              {events.map((event, index) => (
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
                      {event.tags.length > 0 && (
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