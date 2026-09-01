import React, { useEffect, useState } from 'react';
import {
  Search,
  Plus,
  Trash2,
  Volume2,
  Volume1,
  Download,
  PenTool,
  Code,
  BarChart3,
  X,
  Sun,
  Moon
} from 'lucide-react';
import { audioEngine } from '../services/audioEngine';

export const CommandPalette = ({
  isOpen,
  onClose,
  onNewChat,
  onClearThread,
  onToggleSfx,
  onToggleReadAloud,
  onExportThread,
  onTriggerPrompt,
  onSetTheme
}) => {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const commands = [
    {
      id: 'new-chat',
      title: 'New Chat',
      icon: <Plus size={15} />,
      action: () => {
        onNewChat();
        onClose();
      },
    },
    {
      id: 'clear-chat',
      title: 'Clear Conversation',
      icon: <Trash2 size={15} />,
      action: () => {
        onClearThread();
        onClose();
      },
    },
    {
      id: 'export-chat',
      title: 'Export Conversation (.md)',
      icon: <Download size={15} />,
      action: () => {
        onExportThread();
        onClose();
      },
    },
    {
      id: 'prompt-verdict',
      title: 'Search Supreme Court Verdicts',
      icon: <PenTool size={15} />,
      action: () => {
        onTriggerPrompt('What is the Supreme Court verdict in 2025_1_40_61_EN.pdf?');
        onClose();
      },
    },
    {
      id: 'prompt-crpc',
      title: 'Query Section 482 CrPC Rulings',
      icon: <Code size={15} />,
      action: () => {
        onTriggerPrompt('Explain the High Court discretionary powers under Section 482 CrPC.');
        onClose();
      },
    },
    {
      id: 'prompt-precedent',
      title: 'Check Legal Precedents & Appeals',
      icon: <BarChart3 size={15} />,
      action: () => {
        onTriggerPrompt('Under what circumstances can a criminal complaint be restored or quashed?');
        onClose();
      },
    },

    {
      id: 'theme-light',
      title: 'Switch to Light Theme',
      icon: <Sun size={15} />,
      action: () => {
        if (onSetTheme) onSetTheme('light');
        onClose();
      },
    },
    {
      id: 'theme-dark',
      title: 'Switch to Dark Theme',
      icon: <Moon size={15} />,
      action: () => {
        if (onSetTheme) onSetTheme('dark');
        onClose();
      },
    },
    {
      id: 'toggle-sfx',
      title: 'Toggle Sound Effects',
      icon: <Volume2 size={15} />,
      action: () => {
        onToggleSfx();
        onClose();
      },
    },
    {
      id: 'toggle-speech',
      title: 'Toggle Voice Read Aloud',
      icon: <Volume1 size={15} />,
      action: () => {
        onToggleReadAloud();
        onClose();
      },
    },
  ];

  const filteredCommands = commands.filter((c) =>
    c.title.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="cmd-overlay" onClick={onClose}>
      <div className="cmd-modal" onClick={(e) => e.stopPropagation()}>
        <div className="cmd-input-wrapper">
          <Search size={16} color="var(--text-muted)" />
          <input
            className="cmd-input"
            autoFocus
            placeholder="Type a command or search action..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex' }}
          >
            <X size={16} />
          </button>
        </div>

        <div className="cmd-list">
          {filteredCommands.length === 0 ? (
            <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
              No matching commands found.
            </div>
          ) : (
            filteredCommands.map((cmd) => (
              <div
                key={cmd.id}
                className="cmd-item"
                onClick={() => {
                  audioEngine.playSfx('click');
                  cmd.action();
                }}
              >
                {cmd.icon}
                <span>{cmd.title}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
