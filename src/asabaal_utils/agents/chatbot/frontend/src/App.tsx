import React, { useState } from 'react';
import { MessageCircle, Database } from 'lucide-react';
import { ChatView } from './components/ChatView';
import { MemoryView } from './components/MemoryView';

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'memory'>('chat');

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header with tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="flex">
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center space-x-2 px-6 py-3 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'chat'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <MessageCircle className="w-5 h-5" />
            <span>Chat</span>
          </button>
          <button
            onClick={() => setActiveTab('memory')}
            className={`flex items-center space-x-2 px-6 py-3 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'memory'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Database className="w-5 h-5" />
            <span>Memory</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'chat' ? <ChatView /> : <MemoryView />}
      </div>
    </div>
  );
}

export default App;