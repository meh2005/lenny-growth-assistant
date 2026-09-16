import { Plus, MessageSquare, Trash2 } from "lucide-react";

function Sidebar({
  sessions = [],
  activeSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand">
          <div className="brand-mark">L</div>

          <div>
            <h1>Lenny</h1>
            <p>Growth Assistant</p>
          </div>
        </div>

        <button
          className="new-chat-button"
          onClick={onNewChat}
          title="New chat"
        >
          <Plus size={18} />
        </button>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-label">Conversations</div>

        <div className="session-list">
          {sessions.length === 0 ? (
            <p className="empty-sessions">
              No conversations yet.
            </p>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`session-item ${
                  activeSessionId === session.id ? "active" : ""
                }`}
              >
                <button
                  className="session-select"
                  onClick={() => onSelectSession(session.id)}
                >
                  <MessageSquare size={16} />
                  <span>{session.title}</span>
                </button>

                <button
                  className="delete-session"
                  onClick={() => onDeleteSession(session.id)}
                  title="Delete conversation"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="status-dot" />
        <span>Local AI · Ollama</span>
      </div>
    </aside>
  );
}

export default Sidebar;