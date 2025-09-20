import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Settings as SettingsIcon,
  User,
  Shield,
  Bell,
  Database,
  Monitor,
  Save,
  RotateCcw,
  Eye,
  EyeOff,
  Check,
  AlertTriangle,
} from 'lucide-react';

interface SettingsData {
  profile: {
    name: string;
    email: string;
    role: string;
    department: string;
    lastLogin: string;
  };
  api: {
    endpoint: string;
    timeout: number;
    retries: number;
    apiKey: string;
  };
  security: {
    sessionTimeout: number;
    mfaEnabled: boolean;
    passwordExpiry: number;
    auditLogging: boolean;
  };
  notifications: {
    emailAlerts: boolean;
    criticalOnly: boolean;
    digestFrequency: string;
    soundEnabled: boolean;
  };
  display: {
    theme: string;
    language: string;
    timezone: string;
    refreshInterval: number;
  };
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SettingsData>({
    profile: {
      name: 'SOC Analyst',
      email: 'analyst@company.com',
      role: 'Senior Security Analyst',
      department: 'Cybersecurity Operations',
      lastLogin: new Date().toISOString(),
    },
    api: {
      endpoint: 'http://localhost:8000',
      timeout: 30000,
      retries: 3,
      apiKey: 'sk-demo-key-12345',
    },
    security: {
      sessionTimeout: 480,
      mfaEnabled: true,
      passwordExpiry: 90,
      auditLogging: true,
    },
    notifications: {
      emailAlerts: true,
      criticalOnly: false,
      digestFrequency: 'daily',
      soundEnabled: true,
    },
    display: {
      theme: 'dark',
      language: 'en',
      timezone: 'UTC',
      refreshInterval: 30,
    },
  });

  const [unsavedChanges, setUnsavedChanges] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  const updateSetting = (section: keyof SettingsData, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
    setUnsavedChanges(true);
    setSaveStatus('idle');
  };

  const handleSave = async () => {
    setSaveStatus('saving');
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      localStorage.setItem('siem-settings', JSON.stringify(settings));
      setSaveStatus('saved');
      setUnsavedChanges(false);
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (error) {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  };

  const handleReset = () => {
    const savedSettings = localStorage.getItem('siem-settings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
      setUnsavedChanges(false);
      setSaveStatus('idle');
    }
  };

  useEffect(() => {
    const savedSettings = localStorage.getItem('siem-settings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);

  const getSaveButtonContent = () => {
    switch (saveStatus) {
      case 'saving':
        return (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
            Saving...
          </>
        );
      case 'saved':
        return (
          <>
            <Check className="h-4 w-4 mr-2" />
            Saved
          </>
        );
      case 'error':
        return (
          <>
            <AlertTriangle className="h-4 w-4 mr-2" />
            Error
          </>
        );
      default:
        return (
          <>
            <Save className="h-4 w-4 mr-2" />
            Save Changes
          </>
        );
    }
  };

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
            <SettingsIcon className="h-8 w-8 text-neon-blue" />
            <span>Settings</span>
          </h1>
          <p className="text-muted-foreground">
            Configure your SIEM dashboard preferences and system settings
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {unsavedChanges && (
            <Badge variant="outline" className="text-yellow-500 border-yellow-500">
              Unsaved Changes
            </Badge>
          )}
          <Button
            onClick={handleReset}
            variant="outline"
            disabled={!unsavedChanges}
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
          <Button
            onClick={handleSave}
            disabled={!unsavedChanges || saveStatus === 'saving'}
            className={`${
              saveStatus === 'saved'
                ? 'bg-green-600 hover:bg-green-700'
                : saveStatus === 'error'
                ? 'bg-red-600 hover:bg-red-700'
                : ''
            }`}
          >
            {getSaveButtonContent()}
          </Button>
        </div>
      </motion.div>

      {/* Settings Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profile Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="h-5 w-5 text-neon-blue" />
                <span>Profile Information</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground">Name</label>
                <Input
                  value={settings.profile.name}
                  onChange={(e) => updateSetting('profile', 'name', e.target.value)}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground">Email</label>
                <Input
                  value={settings.profile.email}
                  onChange={(e) => updateSetting('profile', 'email', e.target.value)}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground">Role</label>
                <Input
                  value={settings.profile.role}
                  onChange={(e) => updateSetting('profile', 'role', e.target.value)}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground">Department</label>
                <Input
                  value={settings.profile.department}
                  onChange={(e) => updateSetting('profile', 'department', e.target.value)}
                  className="mt-1"
                />
              </div>
              <div className="pt-2 border-t border-accent/20">
                <div className="text-sm text-muted-foreground">
                  Last login: {new Date(settings.profile.lastLogin).toLocaleString()}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* API Configuration */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Database className="h-5 w-5 text-neon-blue" />
                <span>API Configuration</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground">API Endpoint</label>
                <Input
                  value={settings.api.endpoint}
                  onChange={(e) => updateSetting('api', 'endpoint', e.target.value)}
                  className="mt-1"
                  placeholder="http://localhost:8000"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-foreground">Timeout (ms)</label>
                  <Input
                    type="number"
                    value={settings.api.timeout}
                    onChange={(e) => updateSetting('api', 'timeout', parseInt(e.target.value))}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-foreground">Retries</label>
                  <Input
                    type="number"
                    value={settings.api.retries}
                    onChange={(e) => updateSetting('api', 'retries', parseInt(e.target.value))}
                    className="mt-1"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-foreground">API Key</label>
                <div className="relative mt-1">
                  <Input
                    type={showApiKey ? 'text' : 'password'}
                    value={settings.api.apiKey}
                    onChange={(e) => updateSetting('api', 'apiKey', e.target.value)}
                    className="pr-10"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => setShowApiKey(!showApiKey)}
                  >
                    {showApiKey ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Security Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-neon-blue" />
                <span>Security Settings</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground">Session Timeout (minutes)</label>
                <Input
                  type="number"
                  value={settings.security.sessionTimeout}
                  onChange={(e) => updateSetting('security', 'sessionTimeout', parseInt(e.target.value))}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground">Password Expiry (days)</label>
                <Input
                  type="number"
                  value={settings.security.passwordExpiry}
                  onChange={(e) => updateSetting('security', 'passwordExpiry', parseInt(e.target.value))}
                  className="mt-1"
                />
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">Multi-Factor Authentication</span>
                  <Button
                    onClick={() => updateSetting('security', 'mfaEnabled', !settings.security.mfaEnabled)}
                    variant={settings.security.mfaEnabled ? 'default' : 'outline'}
                    size="sm"
                  >
                    {settings.security.mfaEnabled ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">Audit Logging</span>
                  <Button
                    onClick={() => updateSetting('security', 'auditLogging', !settings.security.auditLogging)}
                    variant={settings.security.auditLogging ? 'default' : 'outline'}
                    size="sm"
                  >
                    {settings.security.auditLogging ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Notification Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bell className="h-5 w-5 text-neon-blue" />
                <span>Notifications</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground">Digest Frequency</label>
                <select
                  value={settings.notifications.digestFrequency}
                  onChange={(e) => updateSetting('notifications', 'digestFrequency', e.target.value)}
                  className="w-full mt-1 px-3 py-2 bg-background border border-input rounded-md text-foreground"
                >
                  <option value="realtime">Real-time</option>
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">Email Alerts</span>
                  <Button
                    onClick={() => updateSetting('notifications', 'emailAlerts', !settings.notifications.emailAlerts)}
                    variant={settings.notifications.emailAlerts ? 'default' : 'outline'}
                    size="sm"
                  >
                    {settings.notifications.emailAlerts ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">Critical Events Only</span>
                  <Button
                    onClick={() => updateSetting('notifications', 'criticalOnly', !settings.notifications.criticalOnly)}
                    variant={settings.notifications.criticalOnly ? 'default' : 'outline'}
                    size="sm"
                  >
                    {settings.notifications.criticalOnly ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">Sound Notifications</span>
                  <Button
                    onClick={() => updateSetting('notifications', 'soundEnabled', !settings.notifications.soundEnabled)}
                    variant={settings.notifications.soundEnabled ? 'default' : 'outline'}
                    size="sm"
                  >
                    {settings.notifications.soundEnabled ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Display Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="lg:col-span-2"
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Monitor className="h-5 w-5 text-neon-blue" />
                <span>Display & Interface</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="text-sm font-medium text-foreground">Theme</label>
                  <select
                    value={settings.display.theme}
                    onChange={(e) => updateSetting('display', 'theme', e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-background border border-input rounded-md text-foreground"
                  >
                    <option value="dark">Dark</option>
                    <option value="light">Light</option>
                    <option value="auto">Auto</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-foreground">Language</label>
                  <select
                    value={settings.display.language}
                    onChange={(e) => updateSetting('display', 'language', e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-background border border-input rounded-md text-foreground"
                  >
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="fr">Français</option>
                    <option value="de">Deutsch</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-foreground">Timezone</label>
                  <select
                    value={settings.display.timezone}
                    onChange={(e) => updateSetting('display', 'timezone', e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-background border border-input rounded-md text-foreground"
                  >
                    <option value="UTC">UTC</option>
                    <option value="PST">PST</option>
                    <option value="EST">EST</option>
                    <option value="CET">CET</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-foreground">Refresh Interval (seconds)</label>
                  <Input
                    type="number"
                    value={settings.display.refreshInterval}
                    onChange={(e) => updateSetting('display', 'refreshInterval', parseInt(e.target.value))}
                    className="mt-1"
                    min="5"
                    max="300"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};

export default Settings;