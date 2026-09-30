import { useState } from "react";
import ReactMarkdown from "react-markdown";

export default function ChatBubble({ role, text, error }) {
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  if (role === "user") {
    return <div className="bubble user">{text}</div>;
  }

  return (
    <div className={`bubble bot ${error ? "err" : ""}`}>
      <div className="md">
        <ReactMarkdown>{text}</ReactMarkdown>
      </div>
      {!error && (
        <button className="copy" onClick={copy}>
          {copied ? "Copié ✓" : "Copier"}
        </button>
      )}
    </div>
  );
}