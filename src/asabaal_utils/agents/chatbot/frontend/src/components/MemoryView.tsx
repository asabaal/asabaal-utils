import React, { useState, useEffect } from 'react';
import { Plus, Search, Filter, Edit, Trash2, Save, X, Upload, Download, Tag, Calendar, Eye } from 'lucide-react';
import { MemoryItem, MemoryCreate, MemoryUpdate } from '../types';
import { apiClient } from '../services/api';

export const MemoryView: React.FC = () => {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [filteredMemories, setFilteredMemories] = useState<MemoryItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState<'active' | 'archived' | 'all'>('active');
  const [isLoading, setIsLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingMemory, setEditingMemory] = useState<MemoryItem | null>(null);
  const [expandedMemory, setExpandedMemory] = useState<string | null>(null);
  const [allTags, setAllTags] = useState<string[]>([]);

  // Form states
  const [formData, setFormData] = useState<MemoryCreate>({
    title: '',
    content: '',
    tags: [],
  });
  const [tagInput, setTagInput] = useState('');

  useEffect(() => {
    loadMemories();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [memories, searchQuery, selectedTags, statusFilter]);

  const loadMemories = async () => {
    try {
      setIsLoading(true);
      console.log('Loading memories...');
      const items = await apiClient.getMemoryItems({ status: 'active', limit: 1000 });
      console.log('Loaded memories:', items.length);
      setMemories(items);
      
      // Extract all unique tags
      const tags = new Set<string>();
      items.forEach(item => item.tags.forEach(tag => tags.add(tag)));
      setAllTags(Array.from(tags).sort());
      console.log('Extracted tags:', Array.from(tags));
    } catch (error) {
      console.error('Failed to load memories:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const applyFilters = () => {
    console.log('Applying filters - memories:', memories.length, 'query:', searchQuery, 'tags:', selectedTags);
    let filtered = memories;

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(m => m.status === statusFilter);
      console.log('After status filter:', filtered.length);
    }

    // Search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const beforeSearch = filtered.length;
      filtered = filtered.filter(m => {
        const titleMatch = m.title.toLowerCase().includes(query);
        const contentMatch = m.content.toLowerCase().includes(query);
        return titleMatch || contentMatch;
      });
      console.log(`Search query "${query}": ${beforeSearch} -> ${filtered.length} results`);
      
      // Log first few matches for debugging
      if (filtered.length > 0) {
        console.log('First 3 matches:', filtered.slice(0, 3).map(m => m.title));
      }
    }

    // Tags filter
    if (selectedTags.length > 0) {
      const beforeTags = filtered.length;
      filtered = filtered.filter(m => 
        selectedTags.some(tag => m.tags.includes(tag))
      );
      console.log(`Tags filter ${selectedTags}: ${beforeTags} -> ${filtered.length} results`);
    }

    setFilteredMemories(filtered);
    console.log('Final filtered count:', filtered.length);
  };

  const handleAddMemory = async () => {
    if (!formData.title.trim() || !formData.content.trim()) return;

    try {
      const newMemory = await apiClient.createMemoryItem(formData);
      setMemories(prev => [newMemory, ...prev]);
      setShowAddDialog(false);
      resetForm();
    } catch (error) {
      console.error('Failed to create memory:', error);
    }
  };

  const handleUpdateMemory = async () => {
    if (!editingMemory || !formData.title.trim() || !formData.content.trim()) return;

    try {
      const updates: MemoryUpdate = {
        title: formData.title,
        content: formData.content,
        tags: formData.tags,
      };
      
      const updatedMemory = await apiClient.updateMemoryItem(editingMemory.id, updates);
      setMemories(prev => prev.map(m => m.id === updatedMemory.id ? updatedMemory : m));
      setEditingMemory(null);
      resetForm();
    } catch (error) {
      console.error('Failed to update memory:', error);
    }
  };

  const handleDeleteMemory = async (id: string) => {
    if (!confirm('Are you sure you want to delete this memory item?')) return;
    
    const adminSecret = prompt('Enter admin secret for deletion:');
    if (!adminSecret) return;

    try {
      await apiClient.deleteMemoryItem(id, adminSecret);
      setMemories(prev => prev.filter(m => m.id !== id));
    } catch (error) {
      console.error('Failed to delete memory:', error);
      alert('Failed to delete memory. Check admin secret and try again.');
    }
  };

  const handleImportFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await apiClient.importMemoryFile(file);
      loadMemories(); // Reload memories to show the imported item
    } catch (error) {
      console.error('Failed to import file:', error);
      alert('Failed to import file. Please check the file format and try again.');
    }
  };

  const handleExportMemories = async () => {
    try {
      const exportData = await apiClient.exportMemoryItems();
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `memory-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export memories:', error);
    }
  };

  const resetForm = () => {
    setFormData({ title: '', content: '', tags: [] });
    setTagInput('');
  };

  const startEdit = (memory: MemoryItem) => {
    setEditingMemory(memory);
    setFormData({
      title: memory.title,
      content: memory.content,
      tags: [...memory.tags],
    });
  };

  const addTag = () => {
    const tag = tagInput.trim();
    if (tag && !formData.tags.includes(tag)) {
      setFormData(prev => ({ ...prev, tags: [...prev.tags, tag] }));
      setTagInput('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFormData(prev => ({ 
      ...prev, 
      tags: prev.tags.filter(tag => tag !== tagToRemove) 
    }));
  };

  const toggleTagFilter = (tag: string) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="flex h-full bg-white">
      {/* Left sidebar - Filters */}
      <div className="w-80 border-r border-gray-200 p-4 overflow-y-auto">
        <div className="space-y-6">
          {/* Search */}
          <div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search memories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="active">Active</option>
              <option value="archived">Archived</option>
              <option value="all">All</option>
            </select>
          </div>

          {/* Tags Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {allTags.map(tag => (
                <label key={tag} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedTags.includes(tag)}
                    onChange={() => toggleTagFilter(tag)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm">{tag}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-2">
            <button
              onClick={() => setShowAddDialog(true)}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <Plus className="w-4 h-4" />
              <span>Add Memory</span>
            </button>
            
            <div className="flex space-x-2">
              <label className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 cursor-pointer">
                <Upload className="w-4 h-4" />
                <span className="text-sm">Import</span>
                <input
                  type="file"
                  accept=".txt,.md,.json"
                  onChange={handleImportFile}
                  className="hidden"
                />
              </label>
              
              <button
                onClick={handleExportMemories}
                className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Download className="w-4 h-4" />
                <span className="text-sm">Export</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content - Memory list */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Memories ({filteredMemories.length})
            </h2>
            <button
              onClick={loadMemories}
              className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
            >
              Refresh
            </button>
          </div>

          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading memories...</p>
            </div>
          ) : filteredMemories.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400">
                <Tag className="w-12 h-12 mx-auto mb-4" />
                <p>No memories found</p>
                <p className="text-sm mt-2">
                  {searchQuery ? `No memories match "${searchQuery}"` : 'Try adjusting your filters or add a new memory'}
                </p>
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="mt-2 px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200"
                  >
                    Clear Search
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredMemories.map((memory) => (
                <div key={memory.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{memory.title}</h3>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                        <div className="flex items-center space-x-1">
                          <Calendar className="w-3 h-3" />
                          <span>{formatDate(memory.created_at)}</span>
                        </div>
                        {memory.tags.length > 0 && (
                          <div className="flex items-center space-x-1">
                            <Tag className="w-3 h-3" />
                            <span>{memory.tags.join(', ')}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={() => setExpandedMemory(expandedMemory === memory.id ? null : memory.id)}
                        className="p-1 text-gray-400 hover:text-gray-600"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => startEdit(memory)}
                        className="p-1 text-gray-400 hover:text-blue-600"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteMemory(memory.id)}
                        className="p-1 text-gray-400 hover:text-red-600"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Expanded content */}
                  {expandedMemory === memory.id && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{memory.content}</p>
                      {memory.provenance && (
                        <div className="mt-3 text-xs text-gray-500">
                          <strong>Provenance:</strong> {JSON.stringify(memory.provenance, null, 2)}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add/Edit Dialog */}
      {(showAddDialog || editingMemory) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">
                  {editingMemory ? 'Edit Memory' : 'Add New Memory'}
                </h3>
                <button
                  onClick={() => {
                    setShowAddDialog(false);
                    setEditingMemory(null);
                    resetForm();
                  }}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Memory title..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
                  <textarea
                    value={formData.content}
                    onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-32 resize-none"
                    placeholder="Memory content..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
                  <div className="flex space-x-2 mb-2">
                    <input
                      type="text"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Add a tag..."
                    />
                    <button
                      onClick={addTag}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                    >
                      Add
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {formData.tags.map(tag => (
                      <span
                        key={tag}
                        className="inline-flex items-center space-x-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                      >
                        <span>{tag}</span>
                        <button
                          onClick={() => removeTag(tag)}
                          className="hover:text-blue-900"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowAddDialog(false);
                    setEditingMemory(null);
                    resetForm();
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={editingMemory ? handleUpdateMemory : handleAddMemory}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Save className="w-4 h-4" />
                  <span>{editingMemory ? 'Update' : 'Save'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};