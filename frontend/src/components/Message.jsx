import ReactMarkdown from "react-markdown";

function Message({ role, content }) {
  const isUser = role === "user";

  return (
    <div className={`message-row ${isUser ? "user" : "assistant"}`}>
      <div className="message-bubble">
        <div className="message-role">
          {isUser ? "You" : "Lenny Growth Assistant"}
        </div>

        <div className="message-content">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

export default Message;