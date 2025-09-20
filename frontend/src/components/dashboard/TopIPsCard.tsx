import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Globe, Flag } from 'lucide-react';
import { TopIP } from '../../types';
import { SeverityColors } from '../../services/utils';

interface TopIPsCardProps {
  ips: TopIP[];
  title?: string;
}

const TopIPsCard: React.FC<TopIPsCardProps> = ({ 
  ips, 
  title = "Top Source IPs" 
}) => {
  const getSeverityColor = (level: string) => {
    return SeverityColors[level as keyof typeof SeverityColors] || SeverityColors.low;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      whileHover={{ scale: 1.01 }}
    >
      <Card className="metric-card hover:cyber-glow transition-all duration-300">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Globe className="h-5 w-5 text-neon-blue" />
            <span>{title}</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {ips.slice(0, 5).map((ip, index) => (
              <motion.div
                key={ip.ip}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className="flex items-center justify-between p-3 rounded-lg bg-accent/10 hover:bg-accent/20 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2">
                    <Flag className="h-4 w-4 text-muted-foreground" />
                    <span className="font-mono text-sm text-foreground">
                      {ip.ip}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {ip.country}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-foreground">
                    {ip.count}
                  </span>
                  <Badge
                    className={`${getSeverityColor(ip.threat_level).bg} ${getSeverityColor(ip.threat_level).text} text-xs`}
                  >
                    {ip.threat_level}
                  </Badge>
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default TopIPsCard;