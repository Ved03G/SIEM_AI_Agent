import React from 'react';
import { motion } from 'framer-motion';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Lightbulb, Sparkles } from 'lucide-react';

interface SuggestionChipsProps {
  suggestions: string[];
  onSuggestionClick: (suggestion: string) => void;
  loading?: boolean;
}

const SuggestionChips: React.FC<SuggestionChipsProps> = ({
  suggestions,
  onSuggestionClick,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="flex flex-wrap gap-2 mb-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-8 bg-accent/20 rounded-full animate-pulse"
            style={{ width: `${80 + Math.random() * 40}px` }}
          />
        ))}
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-6"
    >
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center space-x-2 text-sm font-medium">
            <Lightbulb className="h-4 w-4 text-neon-blue" />
            <span>AI Suggestions</span>
            <Badge variant="secondary" className="text-xs">
              Smart Queries
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {suggestions && suggestions.map((suggestion, index) => (
              <motion.div
                key={suggestion}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onSuggestionClick(suggestion)}
                  className="text-xs h-8 px-3 hover:bg-neon-blue/10 hover:border-neon-blue/50 hover:text-neon-blue transition-all duration-200"
                >
                  <Sparkles className="h-3 w-3 mr-1" />
                  {suggestion}
                </Button>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default SuggestionChips;