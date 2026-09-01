import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Mic, MicOff, Paperclip, X } from 'lucide-react';
import { audioEngine } from '../services/audioEngine';

export const ChatInput = ({ onSend, disabled }) => {
  const [text, setText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [attachment, setAttachment] = useState(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [text]);

  const handleSend = () => {
    if ((!text.trim() && !attachment) || disabled) return;
    audioEngine.playSfx('send');

    let fullPrompt = text;
    if (attachment) {
      fullPrompt = `[Attached: ${attachment.name}] ${text}`;
    }

    onSend(fullPrompt);
    setText('');
    setAttachment(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleMic = () => {
    if (isListening) {
      audioEngine.stopListening();
      setIsListening(false);
    } else {
      audioEngine.startListening(
        (transcript) => {
          setText(transcript);
        },
        (listeningState) => {
          setIsListening(listeningState);
        }
      );
    }
  };

  const handleSimulateAttachment = () => {
    audioEngine.playSfx('click');
    setAttachment({
      name: 'notes_document.pdf',
      size: '1.2 MB',
    });
  };

  return (
    <div className="input-container">
      <div className="input-card">
        {attachment && (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '3px 8px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-pill)',
              fontSize: '12px',
              color: 'var(--text-secondary)',
              width: 'fit-content',
            }}
          >
            <Paperclip size={12} />
            <span>{attachment.name}</span>
            <button
              onClick={() => setAttachment(null)}
              style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', display: 'flex' }}
            >
              <X size={12} />
            </button>
          </div>
        )}

        <textarea
          ref={textareaRef}
          className="input-textarea"
          rows={1}
          placeholder="Message Nexus AI... (Enter to send, Shift+Enter for line break)"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />

        <div className="input-bottom-bar">
          <div className="input-tools-left">
            <button
              className={`input-icon-btn ${isListening ? 'listening' : ''}`}
              title={isListening ? 'Stop Voice Listening' : 'Dictate with Voice'}
              onClick={toggleMic}
            >
              {isListening ? <MicOff size={16} /> : <Mic size={16} />}
            </button>

            <button
              className="input-icon-btn"
              title="Attach File"
              onClick={handleSimulateAttachment}
            >
              <Paperclip size={16} />
            </button>
          </div>

          <button
            className="send-btn"
            title="Send Message"
            onClick={handleSend}
            disabled={(!text.trim() && !attachment) || disabled}
          >
            <ArrowUp size={16} />
          </button>
        </div>
      </div>
      <div className="input-disclaimer">
        Nexus AI can make mistakes. Verify important information.
      </div>
    </div>
  );
};
