import React, { useState, useEffect } from 'react';
import {
  X,
  FileText,
  Upload,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Database,
  HardDrive
} from 'lucide-react';
import { fetchDocuments, uploadDocument, triggerReindex, checkBackendHealth } from '../services/chatEngine';

export const DocumentManagerModal = ({ isOpen, onClose }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);
  const [health, setHealth] = useState(null);

  const loadDocsAndHealth = async () => {
    setLoading(true);
    try {
      const h = await checkBackendHealth();
      setHealth(h);
      const d = await fetchDocuments();
      setDocuments(d.documents || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadDocsAndHealth();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setStatusMsg({ type: 'info', text: `Uploading and indexing '${file.name}'...` });

    try {
      const res = await uploadDocument(file);
      setStatusMsg({ type: 'success', text: res.message || `Uploaded ${file.name}` });
      await loadDocsAndHealth();
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Upload failed' });
    } finally {
      setUploading(false);
    }
  };

  const handleReindexAll = async () => {
    setIndexing(true);
    setStatusMsg({ type: 'info', text: 'Scanning & re-indexing all PDF documents in backend data folder...' });

    try {
      const res = await triggerReindex();
      setStatusMsg({
        type: 'success',
        text: `Re-indexing complete! Processed ${res.total_chunks || 0} chunks across documents.`
      });
      await loadDocsAndHealth();
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Indexing failed' });
    } finally {
      setIndexing(false);
    }
  };

  return (
    <div className="cmd-overlay" onClick={onClose}>
      <div
        className="cmd-modal"
        style={{ maxWidth: '640px', width: '90%' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="cmd-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Database size={18} color="var(--accent-primary)" />
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>RAG Knowledge Base Manager</h3>
          </div>
          <button className="tool-button" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {health && (
          <div
            style={{
              padding: '10px 16px',
              margin: '12px 16px 0',
              borderRadius: '8px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              gap: '16px',
              fontSize: '12.5px',
              alignItems: 'center',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className={`status-dot ${health.qdrant ? 'online' : 'offline'}`} />
              <span>Qdrant Vector DB: <strong>{health.qdrant ? 'Connected' : 'Offline'}</strong></span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className={`status-dot ${health.ollama ? 'online' : 'offline'}`} />
              <span>Ollama LLM: <strong>{health.ollama ? 'Connected' : 'Offline'}</strong></span>
            </div>
          </div>
        )}

        {statusMsg && (
          <div
            style={{
              padding: '10px 14px',
              margin: '12px 16px 0',
              borderRadius: '6px',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background:
                statusMsg.type === 'error'
                  ? 'rgba(239,68,68,0.1)'
                  : statusMsg.type === 'success'
                    ? 'rgba(16,185,129,0.1)'
                    : 'rgba(37,99,235,0.1)',
              color:
                statusMsg.type === 'error'
                  ? '#f87171'
                  : statusMsg.type === 'success'
                    ? '#34d399'
                    : '#60a5fa',
              border: `1px solid ${statusMsg.type === 'error'
                ? 'rgba(239,68,68,0.2)'
                : statusMsg.type === 'success'
                  ? 'rgba(16,185,129,0.2)'
                  : 'rgba(37,99,235,0.2)'
                }`,
            }}
          >
            {statusMsg.type === 'success' ? (
              <CheckCircle2 size={14} />
            ) : statusMsg.type === 'error' ? (
              <AlertCircle size={14} />
            ) : (
              <RefreshCw size={14} className="spin" />
            )}
            <span>{statusMsg.text}</span>
          </div>
        )}

        <div style={{ padding: '16px', maxHeight: '360px', overflowY: 'auto' }}>
          <div
            style={{
              display: 'flex',
              justify: 'space-between',
              alignItems: 'center',
              marginBottom: '12px',
            }}
          >
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              PDF Documents in <code>pdf/</code> directory ({documents.length}):
            </span>

            <div style={{ display: 'flex', gap: '8px' }}>
              <label
                className="tool-button"
                style={{ cursor: uploading ? 'not-allowed' : 'pointer', fontSize: '12px', gap: '4px' }}
              >
                <Upload size={13} />
                <span>{uploading ? 'Uploading...' : 'Upload PDF'}</span>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  style={{ display: 'none' }}
                />
              </label>

              <button
                className="tool-button"
                onClick={handleReindexAll}
                disabled={indexing}
                style={{ fontSize: '12px', gap: '4px' }}
              >
                <RefreshCw size={13} className={indexing ? 'spin' : ''} />
                <span>{indexing ? 'Indexing...' : 'Re-index All'}</span>
              </button>
            </div>
          </div>

          {loading ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
              Loading documents...
            </div>
          ) : documents.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No PDF files found in <code>pdf/</code> directory.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {documents.map((doc, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justify: 'space-between',
                    padding: '10px 12px',
                    borderRadius: '6px',
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <FileText size={16} color="var(--accent-primary)" />
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 500 }}>{doc.filename}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {doc.size_mb} MB • Modified: {doc.modified_time}
                      </div>
                    </div>
                  </div>

                  <span
                    style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '12px',
                      background: 'rgba(16,185,129,0.15)',
                      color: 'var(--accent-emerald)',
                      fontWeight: 500,
                    }}
                  >
                    Indexed
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="cmd-footer" style={{ justifyContent: 'flex-end' }}>
          <button className="tool-button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
