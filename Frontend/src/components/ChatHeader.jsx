import React from 'react';
import {
  Menu,
  Volume2,
  VolumeX,
  Volume1,
  Trash2,
  Download,
  Command,
  Sun,
  Moon
} from 'lucide-react';
import { audioEngine } from '../services/audioEngine';

export const ChatHeader = ({
  onToggleSidebar,
  settings,
  onUpdateSettings,
  onClearThread,
  onExportThread,
  onOpenCmd
}) => {
  const isDark = settings.theme === 'dark';

  const toggleTheme = () => {
    audioEngine.playSfx('toggle');
    onUpdateSettings({ theme: isDark ? 'light' : 'dark' });
  };

  const toggleSfx = () => {
    const next = !settings.sfxEnabled;
    audioEngine.setSfxEnabled(next);
    audioEngine.playSfx('toggle');
    onUpdateSettings({ sfxEnabled: next });
  };

  const toggleAutoRead = () => {
    audioEngine.playSfx('toggle');
    onUpdateSettings({ autoReadAloud: !settings.autoReadAloud });
  };

  return (
    <header className="chat-header">
      <div className="header-left">
        <button className="mobile-toggle" onClick={onToggleSidebar} aria-label="Toggle sidebar">
          <Menu size={18} />
        </button>

        <div className="model-badge-select">
          <div className="status-dot online"></div>
          <span>Qwen3:8b (RAG)</span>
        </div>
      </div>

      <div className="header-tools">
        <button
          className="tool-button"
          title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          onClick={toggleTheme}
        >
          {isDark ? <Sun size={15} /> : <Moon size={15} />}
          <span style={{ fontSize: '12px' }}>{isDark ? 'Light' : 'Dark'}</span>
        </button>

        <button
          className={`tool-button ${settings.sfxEnabled ? 'active' : ''}`}
          title="Sound Effects"
          onClick={toggleSfx}
        >
          {settings.sfxEnabled ? <Volume2 size={15} /> : <VolumeX size={15} />}
        </button>

        <button
          className={`tool-button ${settings.autoReadAloud ? 'active' : ''}`}
          title="Voice Read Aloud"
          onClick={toggleAutoRead}
        >
          <Volume1 size={15} />
          <span style={{ fontSize: '12px' }}>Voice</span>
        </button>

        <button className="tool-button" title="Search Commands (Ctrl+K)" onClick={onOpenCmd}>
          <Command size={13} />
          <span style={{ fontSize: '11px', opacity: 0.7 }}>Ctrl+K</span>
        </button>

        <button className="tool-button" title="Export Chat" onClick={onExportThread}>
          <Download size={15} />
        </button>

        <button className="tool-button" title="Clear Conversation" onClick={onClearThread}>
          <Trash2 size={15} />
        </button>
      </div>
    </header>
  );
};


