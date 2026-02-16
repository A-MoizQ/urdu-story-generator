"use client";

import { useEffect, useRef } from "react";
import { ChatMessage } from "@/lib/types";
import ChatBubble from "./ChatBubble";

interface ChatWindowProps {
  messages: ChatMessage[];
}

export default function ChatWindow({ messages }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="neon-border rounded-xl bg-surface-card backdrop-blur-sm overflow-hidden flex flex-col h-[500px] md:h-[550px] scan-line-overlay relative">
      {/* Chat area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <p className="urdu-text font-urdu text-gray-500 text-lg animate-pulse">
              اپنی کہانی شروع کریں ...
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
