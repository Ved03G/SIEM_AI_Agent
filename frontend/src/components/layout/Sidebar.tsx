import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';
import {
  LayoutDashboard,
  Search,
  BarChart3,
  Activity,
  Settings,
  Shield,
} from 'lucide-react';

interface SidebarItem {
  icon: React.ElementType;
  label: string;
  href: string;
  badge?: number;
}

const sidebarItems: SidebarItem[] = [
  {
    icon: LayoutDashboard,
    label: 'Dashboard',
    href: '/',
  },
  {
    icon: Search,
    label: 'Query Console',
    href: '/query',
  },
  {
    icon: BarChart3,
    label: 'Reports',
    href: '/reports',
  },
  {
    icon: Activity,
    label: 'Health',
    href: '/health',
  },
  {
    icon: Settings,
    label: 'Settings',
    href: '/settings',
  },
];

const Sidebar: React.FC = () => {
  const location = useLocation();

  const isActive = (href: string) => {
    if (href === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(href);
  };

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="w-64 bg-card/50 backdrop-blur-sm border-r border-border h-screen sticky top-0"
    >
      <div className="p-6">
        {/* Sidebar Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-2 mb-4">
            <Shield className="h-6 w-6 text-neon-blue" />
            <h2 className="text-lg font-semibold text-foreground">
              Security Center
            </h2>
          </div>
          <div className="text-sm text-muted-foreground">
            AI-Powered SIEM Analysis
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-2">
          {sidebarItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);

            return (
              <Link
                key={item.href}
                to={item.href}
                className={cn(
                  'flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                  active
                    ? 'bg-primary text-primary-foreground shadow-lg cyber-glow'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                )}
              >
                <Icon className="h-5 w-5" />
                <span>{item.label}</span>
                {item.badge && (
                  <span className="ml-auto bg-destructive text-destructive-foreground text-xs px-2 py-1 rounded-full">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Status Section */}
        <div className="mt-8 pt-6 border-t border-border">
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">System Status</span>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-500">Online</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Active Alerts</span>
              <span className="text-red-500 font-medium">8</span>
            </div>
            
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Uptime</span>
              <span className="text-foreground">15d 6h</span>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="mt-6 p-4 bg-accent/20 rounded-lg">
          <div className="text-xs text-muted-foreground mb-2">
            Today's Activity
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="text-center">
              <div className="text-lg font-bold text-neon-blue">2.4K</div>
              <div className="text-xs text-muted-foreground">Events</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-neon-green">42</div>
              <div className="text-xs text-muted-foreground">Alerts</div>
            </div>
          </div>
        </div>
      </div>
    </motion.aside>
  );
};

export default Sidebar;