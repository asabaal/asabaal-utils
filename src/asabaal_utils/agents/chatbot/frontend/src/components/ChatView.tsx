import React, { useState, useEffect, useRef } from 'react';
import { Send, MessageCircle, Brain, Clock } from 'lucide-react';
import { ChatTurn, ChatRequest, UsedMemory } from '../types';
import { apiClient } from '../services/api';

export const ChatView: React.FC = () => {
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [modelsError, setModelsError] = useState<string>('');
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadChatHistory();
    loadModels();
  }, []);

  // Reload models when window regains focus (handles tab switching)
  useEffect(() => {
    const handleFocus = () => {
      if (availableModels.length === 0) {
        loadModels();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [availableModels.length]);

  const loadChatHistory = async () => {
    try {
      const turns = await apiClient.getChatTurns(50);
      setMessages(turns);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const loadModels = async (retryCount = 0) => {
    try {
      setIsLoadingModels(true);
      setModelsError('');
      
      const { models } = await apiClient.getModels();
      console.log('Available chat models:', models);
      setAvailableModels(models);
      if (models.length > 0) {
        setSelectedModel(models[0]);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
      
      // Retry logic - up to 3 attempts with exponential backoff
      if (retryCount < 3) {
        const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s
        console.log(`Retrying models load in ${delay}ms (attempt ${retryCount + 1}/3)`);
        setTimeout(() => loadModels(retryCount + 1), delay);
        return;
      }
      
      // Final failure after retries
      setModelsError('Failed to load models. Please refresh the page.');
      setAvailableModels([]);
      setSelectedModel('');
    } finally {
      setIsLoadingModels(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    try {
      const request: ChatRequest = {
        message: userMessage,
        model: selectedModel || undefined,
        max_tokens: 512,
        temperature: 0.2,
      };

      const response = await apiClient.chatComplete(request);
      
      // Create a new chat turn
      const newTurn: ChatTurn = {
        id: Date.now().toString(),
        ts: new Date().toISOString(),
        user_text: userMessage,
        model_text: response.text,
        memory_hits: response.used_memory,
        prompt_meta: {
          model: selectedModel,
          max_tokens: 512,
          temperature: 0.2,
        },
      };

      setMessages(prev => [...prev, newTurn]);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Add error message
      const errorTurn: ChatTurn = {
        id: Date.now().toString(),
        ts: new Date().toISOString(),
        user_text: userMessage,
        model_text: 'Sorry, I encountered an error while processing your message. Please try again.',
        memory_hits: [],
        prompt_meta: { error: true },
      };
      setMessages(prev => [...prev, errorTurn]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <MessageCircle className="w-6 h-6 text-blue-600" />
            <h1 className="text-xl font-semibold text-gray-900">Chat Assistant</h1>
          </div>
          {isLoadingModels ? (
            <div className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-600 bg-gray-50 flex items-center space-x-2">
              <div className="animate-spin rounded-full h-3 w-3 border-b border-gray-600"></div>
              <span>Loading models...</span>
            </div>
          ) : availableModels.length > 0 ? (
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {availableModels.map(model => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
          ) : (
            <div className="px-3 py-1 border border-red-300 rounded-md text-sm text-red-600 bg-red-50">
              {modelsError || 'No chat models available'}
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <MessageCircle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Start a conversation with your assistant!</p>
            {availableModels.length === 0 && (
              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg max-w-md mx-auto">
                <p className="text-sm text-yellow-800">
                  <strong>{modelsError || 'No chat models available.'}</strong> 
                  {modelsError ? ' Please try again or check your connection.' : ' Please install a chat model in Ollama:'}
                </p>
                {modelsError && (
                  <button
                    onClick={() => loadModels()}
                    className="mt-2 px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700"
                  >
                    Retry Loading Models
                  </button>
                )}
                {!modelsError && (
                  <code className="block mt-2 text-xs bg-yellow-100 p-2 rounded">
                    ollama pull qwen2.5:7b
                  </code>
                )}
              </div>
            )}
          </div>
        ) : (
          messages.map((turn) => (
            <div key={turn.id} className="space-y-2">
              {/* User message */}
              <div className="flex justify-end">
                <div className="max-w-[70%] bg-blue-600 text-white rounded-lg px-4 py-2">
                  <p className="text-sm">{turn.user_text}</p>
                  <div className="flex items-center space-x-1 mt-1 text-xs text-blue-100">
                    <Clock className="w-3 h-3" />
                    <span>{formatTimestamp(turn.ts)}</span>
                  </div>
                </div>
              </div>

              {/* Assistant message */}
              <div className="flex justify-start">
                <div className="max-w-[70%] bg-gray-100 text-gray-900 rounded-lg px-4 py-2">
                  <p className="text-sm whitespace-pre-wrap">{turn.model_text}</p>
                  
                  {/* Memory hits */}
                  {turn.memory_hits && turn.memory_hits.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="flex items-center space-x-1 text-xs text-gray-600 mb-2">
                        <Brain className="w-3 h-3" />
                        <span>Used memory ({turn.memory_hits.length} items):</span>
                      </div>
                      <div className="space-y-1">
                        {turn.memory_hits.map((memory, index) => (
                          <div key={index} className="text-xs bg-white rounded px-2 py-1 border border-gray-200">
                            <span className="font-medium">ID: {memory.id}</span>
                            <span className="text-gray-500 ml-2">(relevance: {memory.score.toFixed(2)})</span>
                            {memory.source_type && (
                              <span className="text-blue-600 ml-2">({memory.source_type})</span>
                            )}
                            {memory.tags && memory.tags.length > 0 && (
                              <span className="text-green-600 ml-2">[{memory.tags.slice(0, 2).join(', ')}]</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center space-x-1 mt-1 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    <span>{formatTimestamp(turn.ts)}</span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm text-gray-600">Thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Send className="w-4 h-4" />
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  );
};