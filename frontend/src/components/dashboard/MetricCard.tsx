import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { cn } from '../../lib/utils';
import { FormatUtils } from '../../services/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  trend?: {
    value: number;
    label: string;
  };
  status?: 'positive' | 'negative' | 'neutral';
  className?: string;
  delay?: number;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon: Icon,
  trend,
  status = 'neutral',
  className,
  delay = 0,
}) => {
  const formatValue = (val: string | number): string => {
    if (typeof val === 'number') {
      return FormatUtils.formatNumber(val);
    }
    return val;
  };

  const getTrendIcon = () => {
    if (!trend) return null;
    
    if (trend.value > 0) {
      return <TrendingUp className="h-3 w-3" />;
    } else if (trend.value < 0) {
      return <TrendingDown className="h-3 w-3" />;
    } else {
      return <Minus className="h-3 w-3" />;
    }
  };

  const getTrendColor = () => {
    if (!trend) return '';
    
    if (status === 'positive') {
      return trend.value > 0 ? 'text-green-500' : 'text-red-500';
    } else if (status === 'negative') {
      return trend.value > 0 ? 'text-red-500' : 'text-green-500';
    } else {
      return 'text-muted-foreground';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ scale: 1.02 }}
      className={cn('group', className)}
    >
      <Card className="metric-card group-hover:cyber-glow transition-all duration-300">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          <div className="relative">
            <Icon className="h-5 w-5 text-muted-foreground group-hover:text-neon-blue transition-colors duration-300" />
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <Icon className="h-5 w-5 text-neon-blue animate-pulse" />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold text-foreground">
              {formatValue(value)}
            </div>
            {trend && (
              <Badge
                variant="secondary"
                className={cn(
                  'flex items-center space-x-1 px-2 py-1',
                  getTrendColor()
                )}
              >
                {getTrendIcon()}
                <span className="text-xs font-medium">
                  {Math.abs(trend.value)}% {trend.label}
                </span>
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default MetricCard;