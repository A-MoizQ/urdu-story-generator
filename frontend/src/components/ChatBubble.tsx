"use client";

import { ChatMessage } from "@/lib/types";

interface ChatBubbleProps {
  message: ChatMessage;
}

export default function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-start" : "justify-end"} message-appear`}>
      <div
        className={`
          max-w-[80%] px-5 py-3 urdu-text font-urdu text-sm relative
          ${message.isStreaming ? "typing-cursor" : ""}
        `}
        style={
          isUser
            ? {
                background: "linear-gradient(135deg, var(--bubble-user-bg1), var(--bubble-user-bg2))",
                border: "1px solid var(--border-color)",
                borderRadius: "0 1rem 1rem 1rem",
                boxShadow: "0 2px 12px rgba(0,0,0,0.2), inset 0 1px 0 rgba(200,169,110,0.1)",
                color: "var(--bubble-user-txt)",
              }
            : {
                background: "linear-gradient(135deg, var(--bubble-ai-bg1), var(--bubble-ai-bg2))",
                border: "1px solid var(--border-color)",
                borderRadius: "1rem 0 1rem 1rem",
                boxShadow: "0 2px 12px rgba(0,0,0,0.2), inset 0 1px 0 rgba(200,169,110,0.08)",
                color: "var(--bubble-ai-txt)",
              }
        }
      >
        {/* Small corner ornament */}
        <span
          className="absolute top-1 text-[8px] opacity-30 select-none"
          style={{ color: "var(--gold)", [isUser ? "right" : "left"]: "6px" }}
        >
          ✦
        </span>

        <p className="leading-relaxed whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}
