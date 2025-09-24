import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
  User,
  Bot,
  Copy,
  RotateCcw,
  MessageSquare,
} from 'lucide-react';
import SuggestionChips from '../components/query/SuggestionChips';
import QueryResults from '../components/query/QueryResults';
import { QueryRequest, QueryResponse, LogEvent } from '../types';
import { apiService } from '../services/api';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  results?: LogEvent[];
  queryStats?: any;
  aiInsights?: string;
  loading?: boolean;
}

const QueryConsole: React.FC = () => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages are added
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [query]);

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
    if (!query.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: query.trim(),
      timestamp: new Date(),
    };

    const loadingMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: 'Analyzing your security data...',
      timestamp: new Date(),
      loading: true,
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setQuery('');
    setLoading(true);

    try {
      const startTime = Date.now();

      const queryRequest: QueryRequest = {
        question: userMessage.content,
        max_results: 50,
        session_id: localStorage.getItem('siem_session_id') || undefined,
      };

      const response: QueryResponse = await apiService.queryLogs(queryRequest);

      const endTime = Date.now();
      const queryTime = endTime - startTime;

      const assistantMessage: ChatMessage = {
        id: loadingMessage.id,
        type: 'assistant',
        content: response.summary || 'Here are the results from your security data search.',
        timestamp: new Date(),
        results: response.results || [],
        queryStats: {
          ...response.query_stats,
          query_time_ms: queryTime,
        },
        aiInsights: response.summary || '',
        loading: false,
      };

      setMessages(prev => prev.map(msg =>
        msg.id === loadingMessage.id ? assistantMessage : msg
      ));

    } catch (error) {
      console.error('Query failed:', error);
      const errorMessage: ChatMessage = {
        id: loadingMessage.id,
        type: 'assistant',
        content: 'Sorry, I encountered an error while searching your security data. Please try again.',
        timestamp: new Date(),
        loading: false,
      };

      setMessages(prev => prev.map(msg =>
        msg.id === loadingMessage.id ? errorMessage : msg
      ));
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

  const clearConversation = async () => {
    try {
      const sid = localStorage.getItem('siem_session_id') || undefined;
      await apiService.clearConversation(sid);
    } catch (e) {
      // ignore
    } finally {
      setMessages([]);
    }
  };

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  return (
    <div className="flex flex-col h-full max-h-screen bg-background">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between p-4 border-b border-border/30 bg-card/30 backdrop-blur-sm"
      >
        <div className="flex items-center space-x-3">
          <Brain className="h-6 w-6 text-neon-blue" />
          <span className="text-xl font-semibold text-foreground">SIEM AI Assistant</span>
          <Badge variant="secondary" className="bg-neon-blue/20 text-neon-blue">
            <Sparkles className="h-3 w-3 mr-1" />
            AI Powered
          </Badge>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={clearConversation}
            className="text-muted-foreground hover:text-foreground"
            disabled={messages.length === 0}
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Clear
          </Button>
        </div>
      </motion.div>

      {/* Chat Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6 min-h-0">
        {messages.length === 0 ? (
          // Welcome Screen
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full space-y-8 max-w-2xl mx-auto"
          >
            <div className="text-center space-y-4">
              <div className="flex items-center justify-center w-16 h-16 rounded-full bg-neon-blue/20 mx-auto">
                <MessageSquare className="h-8 w-8 text-neon-blue" />
              </div>
              <h2 className="text-2xl font-semibold text-foreground">
                How can I help you analyze your security data?
              </h2>
              <p className="text-muted-foreground text-lg">
                Ask me anything about your logs, alerts, and security events in natural language.
              </p>
            </div>

            {/* Suggestion Chips */}
            <SuggestionChips
              suggestions={suggestions}
              onSuggestionClick={handleSuggestionClick}
              loading={suggestionsLoading}
            />

            {/* Example queries */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-4xl">
              {[
                {
                  title: "Recent Security Events",
                  query: "Show me critical alerts from the last 24 hours",
                  icon: "🔴"
                },
                {
                  title: "Failed Authentication",
                  query: "Find failed login attempts from external IPs",
                  icon: "🔐"
                },
                {
                  title: "Network Analysis",
                  query: "Show suspicious network traffic patterns",
                  icon: "🌐"
                },
                {
                  title: "Malware Detection",
                  query: "List malware detections this week",
                  icon: "🦠"
                }
              ].map((example, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 * index }}
                >
                  <Card
                    className="cursor-pointer hover:border-neon-blue/50 transition-all duration-200 bg-card/50 backdrop-blur-sm border-border/30"
                    onClick={() => setQuery(example.query)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start space-x-3">
                        <span className="text-2xl">{example.icon}</span>
                        <div>
                          <h3 className="font-medium text-foreground mb-1">{example.title}</h3>
                          <p className="text-sm text-muted-foreground">{example.query}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </motion.div>
        ) : (
          // Chat Messages
          <div className="space-y-6 max-w-4xl mx-auto w-full">
            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.1 }}
                  className={`flex group ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex space-x-3 max-w-[80%] ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    {/* Avatar */}
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${message.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-neon-blue/20 text-neon-blue'
                      }`}>
                      {message.type === 'user' ? (
                        <User className="h-4 w-4" />
                      ) : (
                        <Bot className="h-4 w-4" />
                      )}
                    </div>

                    {/* Message Content */}
                    <div className={`space-y-2 ${message.type === 'user' ? 'items-end' : 'items-start'} flex-1`}>
                      <div className={`rounded-lg px-4 py-3 ${message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-card border border-border/30'
                        }`}>
                        {message.loading ? (
                          <div className="flex items-center space-x-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-neon-blue" />
                            <span className="text-sm text-muted-foreground">Analyzing...</span>
                          </div>
                        ) : (
                          <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                        )}
                      </div>

                      {/* Results */}
                      {message.results && message.results.length > 0 && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          className="w-full"
                        >
                          <QueryResults
                            events={message.results}
                            loading={false}
                            queryTime={message.queryStats?.query_time_ms || 0}
                            totalCount={message.queryStats?.total_hits || 0}
                            aiInsights={message.aiInsights || ''}
                          />
                        </motion.div>
                      )}

                      {/* Message Actions */}
                      {!message.loading && (
                        <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyMessage(message.content)}
                            className="h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
                          >
                            <Copy className="h-3 w-3 mr-1" />
                            Copy
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="border-t border-border/30 bg-card/30 backdrop-blur-sm p-4"
      >
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end space-x-3">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                placeholder="Ask me about your security data... (e.g., 'Show failed logins from China in the last 24 hours')"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-full resize-none border border-border/30 rounded-lg px-4 py-3 bg-background/50 focus:border-neon-blue/50 focus:ring-neon-blue/20 focus:outline-none transition-colors min-h-[52px] max-h-32"
                disabled={loading}
                rows={1}
              />
            </div>
            <Button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              size="lg"
              className="h-[52px] px-6 bg-neon-blue hover:bg-neon-blue/90 text-black font-medium"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-black" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Quick suggestions when input is focused */}
          {query.length === 0 && !loading && (
            <div className="mt-3 flex flex-wrap gap-2">
              {suggestions.slice(0, 4).map((suggestion, index) => (
                <Button
                  key={index}
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-xs h-7 px-3 text-muted-foreground hover:text-foreground border border-border/30"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default QueryConsole;