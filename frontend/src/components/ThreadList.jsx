import React from 'react';
import { useChatStore } from '../store/index.js';

export const ThreadList = ({ onSelect }) => {
  const { threads, currentThreadId } = useChatStore();

  if (!threads || threads.length === 0) {
    return (
      <div className="thread-list empty">
        <div className="thread-empty">No conversations yet</div>
      </div>
    );
  }

  return (
    <div className="thread-list">
      {threads.map((t) => (
        <button
          key={String(t.id)}
          className={`thread-item ${String(currentThreadId) === String(t.id) ? 'active' : ''}`}
          onClick={() => onSelect(String(t.id))}
          title={t.meta?.title || t.agent_id}
        >
          <div className="thread-title">{t.meta?.title || 'New chat'}</div>
          <div className="thread-subtitle">{t.agent_id}</div>
        </button>
      ))}
    </div>
  );
};

export default ThreadList;


