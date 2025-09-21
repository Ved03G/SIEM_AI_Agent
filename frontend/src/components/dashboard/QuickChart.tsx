import React from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { ChartColors } from '../../services/utils';

interface QuickChartProps {
  title: string;
  data: any[];
  type: 'area' | 'pie';
  dataKey?: string;
  nameKey?: string;
  className?: string;
}

const QuickChart: React.FC<QuickChartProps> = ({
  title,
  data,
  type,
  dataKey = 'count',
  nameKey = 'name',
  className,
}) => {
  const renderAreaChart = () => (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.8} />
            <stop offset="95%" stopColor="#00d4ff" stopOpacity={0.1} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
        <XAxis 
          dataKey={nameKey} 
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#9ca3af', fontSize: 12 }}
        />
        <YAxis 
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#9ca3af', fontSize: 12 }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            border: '1px solid rgba(0, 212, 255, 0.3)',
            borderRadius: '8px',
            color: '#ffffff',
          }}
        />
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke="#00d4ff"
          strokeWidth={2}
          fill="url(#colorGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );

  const renderPieChart = () => (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          paddingAngle={5}
          dataKey={dataKey}
          nameKey={nameKey}
          label={({ name, percentage }) => `${name}: ${percentage}%`}
          labelLine={false}
        >
          {data.map((_, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={ChartColors.cyber[index % ChartColors.cyber.length]} 
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            border: '1px solid rgba(0, 212, 255, 0.3)',
            borderRadius: '8px',
            color: '#ffffff',
          }}
          formatter={(value, name) => [
            `${value} events (${data.find(d => d[nameKey] === name)?.percentage || 0}%)`,
            name
          ]}
        />
      </PieChart>
    </ResponsiveContainer>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className={className}
    >
      <Card className="metric-card hover:cyber-glow transition-all duration-300">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-foreground">
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {type === 'area' ? renderAreaChart() : renderPieChart()}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default QuickChart;