import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Shield, Lock, User } from 'lucide-react';

const Login: React.FC = () => {
  const navigate = useNavigate();

  // Auto-login for demo purposes
  useEffect(() => {
    // Simulate authentication
    localStorage.setItem('auth_token', 'demo_token');
    localStorage.setItem('user_data', JSON.stringify({
      id: '1',
      username: 'security_analyst',
      email: 'analyst@company.com',
      role: 'Senior Security Analyst',
      created_at: new Date().toISOString(),
    }));
    
    // Redirect after a brief moment
    const timer = setTimeout(() => {
      navigate('/');
    }, 2000);

    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-purple-900/20 to-cyan-900/20" />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10"
      >
        <Card className="bg-card/50 backdrop-blur-sm border-border/50 shadow-2xl">
          <CardHeader className="text-center pb-8">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2 }}
              className="flex justify-center mb-4"
            >
              <div className="relative">
                <Shield className="h-16 w-16 text-neon-blue" />
                <div className="absolute inset-0 animate-glow">
                  <Shield className="h-16 w-16 text-neon-blue opacity-50" />
                </div>
              </div>
            </motion.div>
            <CardTitle className="text-2xl font-bold text-foreground">
              SIEM AI Agent
            </CardTitle>
            <p className="text-muted-foreground">
              Security Intelligence Platform
            </p>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="space-y-4"
            >
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Username
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="security_analyst"
                    defaultValue="security_analyst"
                    className="pl-10"
                    disabled
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="password"
                    placeholder="••••••••"
                    defaultValue="password"
                    className="pl-10"
                    disabled
                  />
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-center"
            >
              <div className="flex items-center justify-center space-x-3 mb-4">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-neon-blue"></div>
                <span className="text-neon-blue font-medium">
                  Authenticating...
                </span>
              </div>
              
              <Button 
                disabled 
                className="w-full bg-neon-blue hover:bg-neon-blue/90 text-black font-medium"
              >
                Accessing Security Dashboard
              </Button>
              
              <p className="text-xs text-muted-foreground mt-4">
                Demo Mode - Auto-authentication enabled
              </p>
            </motion.div>
          </CardContent>
        </Card>
        
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="text-center mt-8 text-sm text-muted-foreground"
        >
          <p>🛡️ Advanced Threat Detection • 🤖 AI-Powered Analysis • ⚡ Real-time Monitoring</p>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default Login;