import { useEffect, useRef, useState } from "react";
import { Send, FileText } from "lucide-react";
import axios from "axios";

import Message from "./Message";
import SourcePanel from "./SourcePanel";
import ArtifactViewer from "./ArtifactViewer";

const API_URL = "http://localhost:8000";

function Chat({ sessionId }) {
  const [messages, setMessages] = useState([]);
  const [sources, setSources] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [artifact, setArtifact] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!sessionId) return;

    const loadSession = async () => {
      try {
        const response = await axios.get(
          `${API_URL}/api/sessions/${sessionId}`
        );

        const loadedMessages = response.data.messages || [];

        setMessages(loadedMessages);

        const lastAssistantMessage = [...loadedMessages]
          .reverse()
          .find((message) => message.role === "assistant");

        setSources(lastAssistantMessage?.sources || []);
      } catch (error) {
        console.error("Failed to load session:", error);
      }
    };

    loadSession();
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const sendMessage = async (event) => {
    event.preventDefault();

    const text = input.trim();

    if (!text || !sessionId || loading) {
      return;
    }

    setInput("");
    setArtifact(null);

    const temporaryMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: text,
    };

    setMessages((previous) => [
      ...previous,
      temporaryMessage,
    ]);

    setLoading(true);

    try {
      const response = await axios.post(
        `${API_URL}/api/chat`,
        {
          session_id: sessionId,
          message: text,
        }
      );

      setMessages((previous) => [
        ...previous,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.data.response,
        },
      ]);

      setSources(response.data.sources || []);

      if (response.data.artifact) {
        setArtifact(response.data.artifact);
      }
    } catch (error) {
      console.error("Chat request failed:", error);

      setMessages((previous) => [
        ...previous,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content:
            "I couldn't process that request. Please check that the backend is running and try again.",
        },
      ]);

      setSources([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-layout">
      <main className="chat-main">
        <header className="chat-header">
          <div>
            <h2>Lenny Growth Assistant</h2>
            <p>
              Grounded in Lenny's Podcast transcripts
            </p>
          </div>

          <div className="header-actions">
            <div className="provider-badge">
              ● Ollama
            </div>

            {artifact && (
              <button
                className="artifact-button"
                onClick={() => setArtifact(artifact)}
                title="Open artifact viewer"
              >
                <FileText size={16} />
                Artifact
              </button>
            )}
          </div>
        </header>

        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-mark">L</div>

              <h2>What are you working on?</h2>

              <p>
                Ask about product growth, activation,
                onboarding, retention, PLG, and more.
              </p>

              <div className="suggestions">
                <button
                  onClick={() =>
                    setInput(
                      "How can I improve product activation?"
                    )
                  }
                >
                  Improve product activation
                </button>

                <button
                  onClick={() =>
                    setInput(
                      "How should I think about product-led growth?"
                    )
                  }
                >
                  Understand PLG
                </button>

                <button
                  onClick={() =>
                    setInput(
                      "What are useful onboarding principles?"
                    )
                  }
                >
                  Improve onboarding
                </button>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <Message
                key={message.id}
                role={message.role}
                content={message.content}
              />
            ))
          )}

          {loading && (
            <div className="message-row assistant">
              <div className="message-bubble">
                <div className="message-role">
                  Lenny Growth Assistant
                </div>

                <div className="typing">
                  Searching transcript evidence...
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form
          className="chat-input-area"
          onSubmit={sendMessage}
        >
          <div className="input-wrapper">
            <textarea
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
              placeholder="Ask a growth question..."
              rows={1}
              disabled={loading}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey
                ) {
                  event.preventDefault();
                  sendMessage(event);
                }
              }}
            />

            <button
              type="submit"
              disabled={!input.trim() || loading}
              title="Send message"
            >
              <Send size={18} />
            </button>
          </div>

          <p className="input-hint">
            Answers are grounded in the Lenny Podcast knowledge base.
          </p>
        </form>
      </main>

      {artifact ? (
        <ArtifactViewer
          artifact={artifact}
          onClose={() => setArtifact(null)}
        />
      ) : (
        <SourcePanel sources={sources} />
      )}
    </div>
  );
}

export default Chat;