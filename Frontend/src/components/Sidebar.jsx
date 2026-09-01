import React, { useState } from 'react';
import {
  Sparkles,
  Plus,
  Search,
  Pin,
  Trash2,
  X,
  MessageSquare
} from 'lucide-react';
import { MODELS } from '../services/chatEngine';
import { audioEngine } from '../services/audioEngine';

export const Sidebar = ({
  threads,
  activeThreadId,
  onSelectThread,
  onNewThread,
  onDeleteThread,
  onTogglePin,
  isOpen,
  onCloseMobile,
  settings,
  onUpdateSettings
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredThreads = threads.filter((t) =>
    t.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const pinnedThreads = filteredThreads.filter((t) => t.pinned);
  const otherThreads = filteredThreads.filter((t) => !t.pinned);

  const handleThreadClick = (id) => {
    audioEngine.playSfx('click');
    onSelectThread(id);
    if (onCloseMobile) onCloseMobile();
  };

  const handleNewChat = () => {
    audioEngine.playSfx('click');
    onNewThread();
    if (onCloseMobile) onCloseMobile();
  };

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <div className="logo-box">
          <div className="logo-icon">
            <Sparkles size={18} />
          </div>
          <span>Nexus AI</span>
        </div>
        {onCloseMobile && (
          <button className="mobile-toggle" onClick={onCloseMobile} aria-label="Close menu">
            <X size={18} />
          </button>
        )}
      </div>

      <button className="new-chat-btn" onClick={handleNewChat}>
        <Plus size={16} />
        <span>New Chat</span>
      </button>

      <div className="search-box">
        <div className="search-input-wrapper">
          <Search size={14} />
          <input
            type="text"
            placeholder="Search chats..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="sidebar-threads">
        {pinnedThreads.length > 0 && (
          <div style={{ marginBottom: '8px' }}>
            <div className="section-label">Pinned</div>
            {pinnedThreads.map((thread) => (
              <div
                key={thread.id}
                className={`thread-item ${thread.id === activeThreadId ? 'active' : ''}`}
                onClick={() => handleThreadClick(thread.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                  <MessageSquare size={14} style={{ flexShrink: 0, opacity: 0.7 }} />
                  <span className="thread-title">{thread.title}</span>
                </div>
                <div className="thread-actions" onClick={(e) => e.stopPropagation()}>
                  <button
                    className="icon-action-btn"
                    title="Unpin"
                    onClick={() => onTogglePin(thread.id)}
                  >
                    <Pin size={13} fill="currentColor" />
                  </button>
                  <button
                    className="icon-action-btn"
                    title="Delete"
                    onClick={() => onDeleteThread(thread.id)}
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="section-label">Recent Chats</div>
        {otherThreads.length === 0 && pinnedThreads.length === 0 ? (
          <div style={{ padding: '12px 8px', fontSize: '12.5px', color: 'var(--text-muted)' }}>
            No conversations yet.
          </div>
        ) : (
          otherThreads.map((thread) => (
            <div
              key={thread.id}
              className={`thread-item ${thread.id === activeThreadId ? 'active' : ''}`}
              onClick={() => handleThreadClick(thread.id)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                <MessageSquare size={14} style={{ flexShrink: 0, opacity: 0.7 }} />
                <span className="thread-title">{thread.title}</span>
              </div>
              <div className="thread-actions" onClick={(e) => e.stopPropagation()}>
                <button
                  className="icon-action-btn"
                  title="Pin"
                  onClick={() => onTogglePin(thread.id)}
                >
                  <Pin size={13} />
                </button>
                <button
                  className="icon-action-btn"
                  title="Delete"
                  onClick={() => onDeleteThread(thread.id)}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        <div className="config-group">
          <label className="config-label">Active RAG Engine</label>
          <select
            className="config-select"
            value="qwen3:8b"
            disabled
          >
            <option value="qwen3:8b">
              Qwen 3 (8B RAG - Ollama)
            </option>
          </select>
        </div>
      </div>

    </aside>
  );
};
