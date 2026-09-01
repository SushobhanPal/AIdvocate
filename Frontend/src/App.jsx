import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatHeader } from './components/ChatHeader';
import { ChatWindow } from './components/ChatWindow';
import { ChatInput } from './components/ChatInput';
import { CommandPalette } from './components/CommandPalette';
import {
  getStoredSettings,
  saveStoredSettings,
  getStoredThreads,
  saveStoredThreads,
  getStoredActiveThreadId,
  saveStoredActiveThreadId
} from './services/storage';
import { fetchRAGResponse, streamAiResponse } from './services/chatEngine';
import { audioEngine } from './services/audioEngine';

export function App() {
  const [settings, setSettings] = useState(getStoredSettings);
  const [threads, setThreads] = useState(getStoredThreads);
  const [activeThreadId, setActiveThreadId] = useState(getStoredActiveThreadId);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [isCmdOpen, setIsCmdOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    saveStoredSettings(settings);
    document.documentElement.setAttribute('data-theme', settings.theme);
    audioEngine.setSfxEnabled(settings.sfxEnabled);
  }, [settings]);

  useEffect(() => {
    saveStoredThreads(threads);
  }, [threads]);

  useEffect(() => {
    saveStoredActiveThreadId(activeThreadId);
  }, [activeThreadId]);

  const activeThread = threads.find((t) => t.id === activeThreadId) || threads[0] || {
    id: 'default-thread',
    title: 'New Chat',
    messages: [],
  };

  const handleUpdateSettings = (newSettings) => {
    setSettings((prev) => ({ ...prev, ...newSettings }));
  };

  const handleNewThread = () => {
    const newId = `thread-${Date.now()}`;
    const newThread = {
      id: newId,
      title: 'New Conversation',
      createdAt: Date.now(),
      pinned: false,
      messages: [],
    };
    setThreads((prev) => [newThread, ...prev]);
    setActiveThreadId(newId);
  };

  const handleDeleteThread = (id) => {
    setThreads((prev) => {
      const filtered = prev.filter((t) => t.id !== id);
      if (id === activeThreadId && filtered.length > 0) {
        setActiveThreadId(filtered[0].id);
      }
      return filtered.length > 0 ? filtered : [
        { id: `thread-${Date.now()}`, title: 'New Conversation', createdAt: Date.now(), pinned: false, messages: [] }
      ];
    });
  };

  const handleTogglePin = (id) => {
    setThreads((prev) =>
      prev.map((t) => (t.id === id ? { ...t, pinned: !t.pinned } : t))
    );
  };

  const handleSendPrompt = async (promptText) => {
    if (!promptText.trim() || isStreaming) return;

    const userMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      timestamp: Date.now(),
      content: promptText,
    };

    const isFirstMsg = activeThread.messages.length === 0;
    const threadTitle = isFirstMsg ? promptText.slice(0, 24) + '...' : activeThread.title;

    setThreads((prev) =>
      prev.map((t) =>
        t.id === activeThreadId
          ? {
            ...t,
            title: threadTitle,
            messages: [...t.messages, userMessage],
          }
          : t
      )
    );

    setIsStreaming(true);
    setStreamingContent('');
    audioEngine.playSfx('receive');

    const ragResponse = await fetchRAGResponse(promptText);

    await streamAiResponse(ragResponse.answer, (chunk) => {
      setStreamingContent(chunk);
    });

    const aiMessage = {
      id: `ai-${Date.now()}`,
      sender: 'ai',
      timestamp: Date.now(),
      content: ragResponse.answer,
      sources: ragResponse.sources || [],
      model: 'qwen3:8b',
    };

    setThreads((prev) =>
      prev.map((t) =>
        t.id === activeThreadId
          ? {
            ...t,
            messages: [...t.messages, aiMessage],
          }
          : t
      )
    );

    setIsStreaming(false);
    setStreamingContent('');

    if (settings.autoReadAloud) {
      audioEngine.speakText(ragResponse.answer);
    }
  };

  const handleRegenerate = () => {
    if (activeThread.messages.length < 2) return;
    const lastUserMsgIndex = [...activeThread.messages]
      .reverse()
      .findIndex((m) => m.sender === 'user');

    if (lastUserMsgIndex !== -1) {
      const realIndex = activeThread.messages.length - 1 - lastUserMsgIndex;
      const lastUserPrompt = activeThread.messages[realIndex].content;

      setThreads((prev) =>
        prev.map((t) =>
          t.id === activeThreadId
            ? { ...t, messages: t.messages.slice(0, realIndex + 1) }
            : t
        )
      );

      handleSendPrompt(lastUserPrompt);
    }
  };

  const handleClearThread = () => {
    audioEngine.playSfx('click');
    setThreads((prev) =>
      prev.map((t) => (t.id === activeThreadId ? { ...t, messages: [] } : t))
    );
  };

  const handleExportThread = () => {
    audioEngine.playSfx('click');
    const mdContent = `# ${activeThread.title}\n\n` +
      activeThread.messages
        .map((m) => `### ${m.sender === 'user' ? 'User' : 'RAG AI'}\n${m.content}\n`)
        .join('\n---\n\n');

    const blob = new Blob([mdContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeThread.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="app-container">
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        onSelectThread={setActiveThreadId}
        onNewThread={handleNewThread}
        onDeleteThread={handleDeleteThread}
        onTogglePin={handleTogglePin}
        isOpen={isSidebarOpen}
        onCloseMobile={() => setIsSidebarOpen(false)}
        settings={settings}
        onUpdateSettings={handleUpdateSettings}
      />

      <main className="main-chat">
        <ChatHeader
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          settings={settings}
          onUpdateSettings={handleUpdateSettings}
          onClearThread={handleClearThread}
          onExportThread={handleExportThread}
          onOpenCmd={() => setIsCmdOpen(true)}
        />

        <ChatWindow
          messages={activeThread.messages}
          isStreaming={isStreaming}
          streamingContent={streamingContent}
          onSendPrompt={handleSendPrompt}
          onRegenerate={handleRegenerate}
          activeModel="qwen3:8b"
        />

        <ChatInput onSend={handleSendPrompt} disabled={isStreaming} />
      </main>

      <CommandPalette
        isOpen={isCmdOpen}
        onClose={() => setIsCmdOpen(false)}
        onNewChat={handleNewThread}
        onClearThread={handleClearThread}
        onToggleSfx={() => handleUpdateSettings({ sfxEnabled: !settings.sfxEnabled })}
        onToggleReadAloud={() => handleUpdateSettings({ autoReadAloud: !settings.autoReadAloud })}
        onExportThread={handleExportThread}
        onTriggerPrompt={handleSendPrompt}
        onSetTheme={(theme) => handleUpdateSettings({ theme })}
      />
    </div>
  );
}

export default App;

