import React, { useState } from 'react';
import {
  User,
  Copy,
  Check,
  RotateCcw,
  Volume2,
  ThumbsUp,
  ThumbsDown,
  FileText
} from 'lucide-react';
import { audioEngine } from '../services/audioEngine';

export const MessageBubble = ({ message, onRegenerate, isLastAiMessage }) => {
  const isUser = message.sender === 'user';
  const [copied, setCopied] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [liked, setLiked] = useState(null);

  const handleCopyText = (text) => {
    navigator.clipboard.writeText(text);
    audioEngine.playSfx('click');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSpeak = () => {
    if (isSpeaking) {
      audioEngine.stopSpeech();
      setIsSpeaking(false);
    } else {
      setIsSpeaking(true);
      audioEngine.speakText(message.content, () => setIsSpeaking(false));
    }
  };

  const renderMessageContent = (content) => {
    return (
      <div className="markdown-body">
        {renderFormattedText(content)}
      </div>
    );
  };


  const renderSvgChart = (jsonStr) => {
    try {
      const chartData = JSON.parse(jsonStr);
      return (
        <div className="chart-widget">
          <div className="chart-title">{chartData.title}</div>
          <svg className="svg-chart" viewBox="0 0 400 160">
            <line x1="40" y1="20" x2="380" y2="20" stroke="var(--border-subtle)" strokeDasharray="3" />
            <line x1="40" y1="60" x2="380" y2="60" stroke="var(--border-subtle)" strokeDasharray="3" />
            <line x1="40" y1="100" x2="380" y2="100" stroke="var(--border-subtle)" strokeDasharray="3" />
            <line x1="40" y1="140" x2="380" y2="140" stroke="var(--border-medium)" />

            {chartData.labels.map((label, idx) => (
              <text
                key={idx}
                x={70 + idx * 85}
                y="155"
                fill="var(--text-muted)"
                fontSize="11"
                textAnchor="middle"
              >
                {label}
              </text>
            ))}

            {chartData.series.map((s, sIdx) => {
              const points = s.values
                .map((val, idx) => `${70 + idx * 85},${140 - (val / 130) * 110}`)
                .join(' ');
              return (
                <g key={sIdx}>
                  <polyline
                    fill="none"
                    stroke={s.color}
                    strokeWidth="2.5"
                    points={points}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  {s.values.map((val, idx) => (
                    <circle
                      key={idx}
                      cx={70 + idx * 85}
                      cy={140 - (val / 130) * 110}
                      r="4"
                      fill={s.color}
                    />
                  ))}
                </g>
              );
            })}
          </svg>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginTop: '10px' }}>
            {chartData.series.map((s, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11.5px', color: 'var(--text-secondary)' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: s.color }}></span>
                {s.name}
              </div>
            ))}
          </div>
        </div>
      );
    } catch {
      return null;
    }
  };

  const renderFormattedText = (text) => {
    const parts = text.split(/(```[\s\S]*?```)/g);

    return parts.map((part, index) => {
      if (part.startsWith('```')) {
        const firstLineEnd = part.indexOf('\n');
        const lang = part.substring(3, firstLineEnd).trim() || 'code';
        const codeContent = part.substring(firstLineEnd + 1, part.length - 3);

        return (
          <div key={index} className="code-block-wrapper">
            <div className="code-header">
              <span>{lang.toUpperCase()}</span>
              <button className="copy-code-btn" onClick={() => handleCopyText(codeContent)}>
                <Copy size={12} />
                <span>Copy Code</span>
              </button>
            </div>
            <pre>
              <code>{codeContent}</code>
            </pre>
          </div>
        );
      } else {
        return part.split('\n\n').map((paragraph, pIdx) => {
          if (paragraph.startsWith('### ')) {
            return <h3 key={pIdx}>{paragraph.slice(4)}</h3>;
          }
          if (paragraph.startsWith('## ')) {
            return <h2 key={pIdx}>{paragraph.slice(3)}</h2>;
          }
          if (paragraph.startsWith('# ')) {
            return <h1 key={pIdx}>{paragraph.slice(2)}</h1>;
          }
          if (paragraph.startsWith('> ')) {
            return (
              <blockquote key={pIdx}>
                {paragraph.slice(2)}
              </blockquote>
            );
          }

          if (paragraph.includes('\n- ') || paragraph.startsWith('- ')) {
            const items = paragraph.split('\n- ').map(i => i.replace(/^- /, ''));
            return (
              <ul key={pIdx}>
                {items.map((item, iIdx) => (
                  <li key={iIdx}>{renderInlineFormatting(item)}</li>
                ))}
              </ul>
            );
          }

          return <p key={pIdx}>{renderInlineFormatting(paragraph)}</p>;
        });
      }
    });
  };

  const renderInlineFormatting = (str) => {
    return str.split(/(\*\*.*?\*\*|`.*?`)/g).map((chunk, cIdx) => {
      if (chunk.startsWith('**') && chunk.endsWith('**')) {
        return <strong key={cIdx}>{chunk.slice(2, -2)}</strong>;
      }
      if (chunk.startsWith('`') && chunk.endsWith('`')) {
        return <code key={cIdx}>{chunk.slice(1, -1)}</code>;
      }
      return chunk;
    });
  };

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'ai'}`}>
      <div className="message-bubble-content">
        {!isUser && (
          <div className="message-header">
            <span className="model-tag">{message.model || 'Nexus AI'}</span>
            <span>{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
        )}

        <div className="message-bubble">
          {renderMessageContent(message.content)}

          {!isUser && message.sources && message.sources.length > 0 && (
            <div
              style={{
                marginTop: '12px',
                paddingTop: '10px',
                borderTop: '1px solid var(--border-subtle)',
                fontSize: '12px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  color: 'var(--text-secondary)',
                  fontWeight: 500,
                  marginBottom: '8px',
                }}
              >
                <FileText size={13} color="var(--accent-primary)" />
                <span>Retrieved Context Sources ({message.sources.length})</span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {message.sources.map((src, idx) => (
                  <div
                    key={idx}
                    title={src.snippet}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      background: 'var(--bg-tertiary)',
                      border: '1px solid var(--border-medium)',
                      fontSize: '11.5px',
                      color: 'var(--text-primary)',
                      cursor: 'help',
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>📄 {src.filename}</span>
                    <span style={{ opacity: 0.6 }}>•</span>
                    <span style={{ color: 'var(--accent-primary)', fontWeight: 500 }}>
                      Page {src.page}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>


        {!isUser && (
          <div className="message-actions">
            <button
              className="action-icon-btn"
              title="Copy text"
              onClick={() => handleCopyText(message.content)}
            >
              {copied ? <Check size={13} color="var(--accent-emerald)" /> : <Copy size={13} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              className={`action-icon-btn ${isSpeaking ? 'active' : ''}`}
              title="Read aloud"
              onClick={handleSpeak}
            >
              <Volume2 size={13} />
              <span>{isSpeaking ? 'Stop' : 'Listen'}</span>
            </button>

            {isLastAiMessage && (
              <button className="action-icon-btn" title="Regenerate response" onClick={onRegenerate}>
                <RotateCcw size={13} />
                <span>Retry</span>
              </button>
            )}

            <button
              className="action-icon-btn"
              title="Good response"
              onClick={() => {
                audioEngine.playSfx('click');
                setLiked(liked === 'up' ? null : 'up');
              }}
              style={{ color: liked === 'up' ? 'var(--accent-primary)' : 'inherit' }}
            >
              <ThumbsUp size={13} />
            </button>

            <button
              className="action-icon-btn"
              title="Bad response"
              onClick={() => {
                audioEngine.playSfx('click');
                setLiked(liked === 'down' ? null : 'down');
              }}
              style={{ color: liked === 'down' ? 'var(--accent-danger)' : 'inherit' }}
            >
              <ThumbsDown size={13} />
            </button>
          </div>
        )}
      </div>

      {isUser && (
        <div className="avatar user">
          <User size={16} />
        </div>
      )}
    </div>
  );
};
