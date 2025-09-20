import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import {
  Search,
  Sparkles,
  Brain,
  Zap,
  History,
  BookOpen,
  Send,
} from 'lucide-react';
import SuggestionChips from '../components/query/SuggestionChips';
import QueryResults from '../components/query/QueryResults';
import { QueryRequest, QueryResponse, LogEvent } from '../types';
import { apiService } from '../services/api';

const QueryConsole: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<LogEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(true);
  const [queryTime, setQueryTime] = useState<number>(0);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [aiInsights, setAiInsights] = useState<string>('');
  const [queryHistory, setQueryHistory] = useState<string[]>([]);

  // Load suggestions on component mount
  useEffect(() => {
    const loadSuggestions = async () => {
      try {
        setSuggestionsLoading(true);
        const suggestionData = await apiService.getSuggestions();
        setSuggestions(suggestionData.suggestions);
      } catch (error) {
        console.error('Failed to load suggestions:', error);
        // Fallback suggestions
        setSuggestions([
          'Show failed logins in last 24 hours',
          'Find suspicious network traffic',
          'List critical security alerts',
          'Show login attempts from foreign IPs',
          'Find malware detections this week',
          'Show privilege escalation attempts',
          'List blocked network connections',
          'Find unusual user activity',
        ]);
      } finally {
        setSuggestionsLoading(false);
      }
    };

    loadSuggestions();
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;

    try {
      setLoading(true);
      const startTime = Date.now();
      
      const queryRequest: QueryRequest = {
        query: query.trim(),
        limit: 50,
      };

      const response: QueryResponse = await apiService.queryLogs(queryRequest);
      
      const endTime = Date.now();
      setQueryTime(endTime - startTime);
      
      setResults(response.events);
      setTotalCount(response.total_count);
      setAiInsights(response.ai_insights || '');
      
      // Add to history
      if (!queryHistory.includes(query.trim())) {
        setQueryHistory(prev => [query.trim(), ...prev.slice(0, 9)]);
      }
      
    } catch (error) {
      console.error('Query failed:', error);
      setResults([]);
      setTotalCount(0);
      setAiInsights('');
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
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
            <Brain className="h-8 w-8 text-neon-blue" />
            <span>AI Query Console</span>
          </h1>
          <p className="text-muted-foreground">
            Ask questions in natural language about your security data
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="secondary" className="bg-neon-blue/20 text-neon-blue">
            <Sparkles className="h-3 w-3 mr-1" />
            AI Powered
          </Badge>
          <Badge variant="outline">
            <Zap className="h-3 w-3 mr-1" />
            Real-time
          </Badge>
        </div>
      </motion.div>

      {/* Query Input */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="bg-card/50 backdrop-blur-sm border-2 border-border/50 hover:border-neon-blue/50 transition-all duration-300 cyber-glow">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Search className="h-5 w-5 text-neon-blue" />
              <span>Natural Language Query</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex space-x-4">
              <div className="flex-1">
                <Input
                  placeholder="Ask me anything about your security data... (e.g., 'Show me failed logins from China in the last 24 hours')"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="h-12 text-base bg-background/50 border-border/50 focus:border-neon-blue/50 focus:ring-neon-blue/20"
                  disabled={loading}
                />
              </div>
              <Button
                onClick={handleSearch}
                disabled={loading || !query.trim()}
                size="lg"
                className="h-12 px-6 bg-neon-blue hover:bg-neon-blue/90 text-black font-medium"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-black" />
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Analyze
                  </>
                )}
              </Button>
            </div>
            
            {/* Query Examples */}
            <div className="mt-4 text-sm text-muted-foreground">
              <span className="font-medium">Example queries:</span>
              <div className="mt-1 flex flex-wrap gap-2">
                {[
                  "Failed logins from Russia",
                  "Malware detections this week",
                  "Unusual network activity"
                ].map((example) => (
                  <button
                    key={example}
                    onClick={() => setQuery(example)}
                    className="text-neon-blue hover:underline"
                  >
                    "{example}"
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* AI Suggestions */}
      <SuggestionChips
        suggestions={suggestions}
        onSuggestionClick={handleSuggestionClick}
        loading={suggestionsLoading}
      />

      {/* Query History */}
      {queryHistory.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-card/30 backdrop-blur-sm border-border/30">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center space-x-2 text-sm font-medium">
                <History className="h-4 w-4 text-muted-foreground" />
                <span>Recent Queries</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {queryHistory.slice(0, 5).map((historyQuery, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    size="sm"
                    onClick={() => setQuery(historyQuery)}
                    className="text-xs h-7 px-2 text-muted-foreground hover:text-foreground"
                  >
                    {historyQuery.length > 50 ? `${historyQuery.substring(0, 50)}...` : historyQuery}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Results */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <QueryResults
          events={results}
          loading={loading}
          queryTime={queryTime}
          totalCount={totalCount}
          aiInsights={aiInsights}
        />
      </motion.div>

      {/* Help Section */}
      {results.length === 0 && !loading && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card className="bg-gradient-to-r from-blue-900/10 to-purple-900/10 border-blue-500/20">
            <CardContent className="p-6">
              <div className="flex items-start space-x-4">
                <BookOpen className="h-6 w-6 text-blue-400 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    How to use the AI Query Console
                  </h3>
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <p>
                      <strong className="text-blue-400">Natural Language:</strong> Ask questions as you would to a security analyst
                    </p>
                    <p>
                      <strong className="text-blue-400">Time Ranges:</strong> "last 24 hours", "this week", "yesterday"
                    </p>
                    <p>
                      <strong className="text-blue-400">Locations:</strong> "from China", "outside US", "internal networks"
                    </p>
                    <p>
                      <strong className="text-blue-400">Event Types:</strong> "failed logins", "malware", "network anomalies"
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
};

export default QueryConsole;