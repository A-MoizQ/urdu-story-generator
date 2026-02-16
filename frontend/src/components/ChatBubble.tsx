"use client";

import { ChatMessage } from "@/lib/types";

interface ChatBubbleProps {
  message: ChatMessage;
}

export default function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex ${isUser ? "justify-start" : "justify-end"} message-appear`}
    >
      <div
        className={`
          max-w-[80%] rounded-2xl px-5 py-3 urdu-text font-urdu text-sm
          ${
            isUser
              ? "bg-surface-lighter neon-border text-gray-100"
              : "bg-gradient-to-br from-surface-light to-surface neon-border-cyan text-gray-200"
          }
          ${message.isStreaming ? "typing-cursor" : ""}
        `}
      >
        <p className="leading-relaxed whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}
