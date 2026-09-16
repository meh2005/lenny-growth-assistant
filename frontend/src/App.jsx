import { useEffect, useState } from "react";
import axios from "axios";

import Sidebar from "./components/Sidebar";
import Chat from "./components/Chat";

const API_URL = "http://localhost:8000";

function App() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadSessions = async () => {
    try {
      const response = await axios.get(
        `${API_URL}/api/sessions`
      );

      const data = response.data || [];

      setSessions(data);

      if (data.length > 0 && !activeSessionId) {
        setActiveSessionId(data[0].id);
      }
    } catch (error) {
      console.error("Failed to load sessions:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const createNewChat = async () => {
    try {
      const response = await axios.post(
        `${API_URL}/api/sessions`,
        {
          user_name: "Guest",
          title: "New Chat",
        }
      );

      const newSession = response.data;

      setSessions((previous) => [
        newSession,
        ...previous,
      ]);

      setActiveSessionId(newSession.id);
    } catch (error) {
      console.error("Failed to create session:", error);
    }
  };

  const selectSession = (sessionId) => {
    setActiveSessionId(sessionId);
  };

  const deleteSession = async (sessionId) => {
    try {
      await axios.delete(
        `${API_URL}/api/sessions/${sessionId}`
      );

      const remaining = sessions.filter(
        (session) => session.id !== sessionId
      );

      setSessions(remaining);

      if (activeSessionId === sessionId) {
        setActiveSessionId(
          remaining.length > 0
            ? remaining[0].id
            : null
        );
      }
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  };

  if (loading) {
    return (
      <div className="app-loading">
        Loading Lenny Growth Assistant...
      </div>
    );
  }

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onNewChat={createNewChat}
        onSelectSession={selectSession}
        onDeleteSession={deleteSession}
      />

      {activeSessionId ? (
        <Chat sessionId={activeSessionId} />
      ) : (
        <main className="empty-chat">
          <div>
            <div className="empty-chat-mark">L</div>

            <h2>Welcome to Lenny Growth Assistant</h2>

            <p>
              Create a conversation to start asking
              growth questions grounded in Lenny's
              Podcast transcripts.
            </p>

            <button onClick={createNewChat}>
              Start a new conversation
            </button>
          </div>
        </main>
      )}
    </div>
  );
}

export default App;