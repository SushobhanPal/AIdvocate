import React, { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { Sparkles, Code, PenTool, BarChart3, Lightbulb } from 'lucide-react';

export const ChatWindow = ({
  messages,
  isStreaming,
  streamingContent,
  onSendPrompt,
  onRegenerate,
  activeModel
}) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const quickPrompts = [
    {
      title: 'Supreme Court Verdicts',
      desc: 'Query case decisions and judgment summaries.',
      prompt: 'What is the Supreme Court verdict in 2025_1_40_61_EN.pdf?',
    },
    {
      title: 'Section 482 CrPC Powers',
      desc: 'Explore High Court discretionary jurisdiction rules.',
      prompt: 'Explain the High Court discretionary powers under Section 482 CrPC.',
    },
    {
      title: 'Quashing Proceedings',
      desc: 'Understand legal grounds for quashing criminal complaints.',
      prompt: 'Under what circumstances can a criminal complaint be restored or quashed?',
    },
    {
      title: 'Negotiable Instruments Act',
      desc: 'Check precedents regarding power of attorney holders.',
      prompt: 'Summarize Supreme Court rulings regarding Power of Attorney holders in legal cases.',
    },
  ];


  return (
    <div className="messages-container">
      <div className="messages-inner">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <div className="welcome-icon-box">
              {/* <Sparkles size={26} /> */}
            </div>
            <div className="welcome-title">How can I help you today?</div>
            <div className="welcome-subtitle">
              Ask anything, write code, draft documents, or pick a prompt below to get started.
            </div>

            <div className="prompt-suggestions">
              {quickPrompts.map((card, idx) => (
                <div
                  key={idx}
                  className="suggestion-card"
                  onClick={() => onSendPrompt(card.prompt)}
                >
                  <div className="suggestion-title">
                    <span>{card.title}</span>
                  </div>
                  <div className="suggestion-desc">{card.desc}</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <MessageBubble
                key={msg.id || idx}
                message={msg}
                onRegenerate={onRegenerate}
                isLastAiMessage={idx === messages.length - 1 && msg.sender === 'ai'}
              />
            ))}

            {isStreaming && (
              <MessageBubble
                message={{
                  id: 'streaming',
                  sender: 'ai',
                  timestamp: Date.now(),
                  content: streamingContent || 'Thinking...',
                  model: activeModel,
                }}
                onRegenerate={() => { }}
                isLastAiMessage={false}
              />
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
