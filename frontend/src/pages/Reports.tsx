import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  BarChart3,
  FileText,
  Download,
  Calendar,
  Filter,
  TrendingUp,
} from 'lucide-react';

const Reports: React.FC = () => {
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
            <BarChart3 className="h-8 w-8 text-neon-blue" />
            <span>Security Reports</span>
          </h1>
          <p className="text-muted-foreground">
            Generate comprehensive security analysis reports
          </p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Date Range
          </Button>
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
          <Button size="sm" className="bg-neon-blue hover:bg-neon-blue/90 text-black">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </motion.div>

      {/* Report Templates */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[
          {
            title: 'Authentication Failures',
            description: 'Failed login attempts and brute force attacks',
            icon: '🔐',
            count: '2,341 events',
            trend: '+12%',
          },
          {
            title: 'Malware Detections',
            description: 'Virus, trojans, and malicious file analysis',
            icon: '🦠',
            count: '89 threats',
            trend: '-5%',
          },
          {
            title: 'Network Anomalies',
            description: 'Suspicious network traffic and connections',
            icon: '🌐',
            count: '456 incidents',
            trend: '+8%',
          },
          {
            title: 'User Activity',
            description: 'User behavior and access pattern analysis',
            icon: '👤',
            count: '1,234 users',
            trend: '+3%',
          },
          {
            title: 'Threat Intelligence',
            description: 'IOCs, threat actor analysis, and attribution',
            icon: '🕵️',
            count: '67 indicators',
            trend: '+15%',
          },
          {
            title: 'Compliance Report',
            description: 'Regulatory compliance and audit trails',
            icon: '📋',
            count: '100% compliant',
            trend: '0%',
          },
        ].map((report, index) => (
          <motion.div
            key={report.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.02 }}
          >
            <Card className="metric-card hover:cyber-glow transition-all duration-300 cursor-pointer">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{report.icon}</span>
                    <span className="text-lg">{report.title}</span>
                  </div>
                  <Badge
                    variant={report.trend.startsWith('+') ? 'default' : 'secondary'}
                    className="text-xs"
                  >
                    <TrendingUp className="h-3 w-3 mr-1" />
                    {report.trend}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-3">
                  {report.description}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-lg font-bold text-neon-blue">
                    {report.count}
                  </span>
                  <Button size="sm" variant="outline">
                    <FileText className="h-3 w-3 mr-1" />
                    Generate
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Coming Soon Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
      >
        <Card className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 border-purple-500/30">
          <CardContent className="p-8 text-center">
            <BarChart3 className="h-16 w-16 text-purple-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-foreground mb-2">
              Advanced Reporting Coming Soon
            </h3>
            <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
              Interactive charts, customizable dashboards, scheduled reports, and AI-powered insights 
              are being developed to give you the most comprehensive security reporting experience.
            </p>
            <div className="flex justify-center space-x-4">
              <Button variant="outline">
                <FileText className="h-4 w-4 mr-2" />
                View Sample Report
              </Button>
              <Button className="bg-neon-blue hover:bg-neon-blue/90 text-black">
                <Download className="h-4 w-4 mr-2" />
                Request Beta Access
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default Reports;