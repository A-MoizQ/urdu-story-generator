"use client";

import { useState, useCallback } from "react";
import Header from "@/components/Header";
import TeamSidebar from "@/components/TeamSidebar";
import ChatWindow from "@/components/ChatWindow";
import InputBar from "@/components/InputBar";
import { ChatMessage, SYSTEM_GREETING } from "@/lib/types";
import { streamGenerate } from "@/lib/api";

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([SYSTEM_GREETING]);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSend = useCallback(
    async (text: string) => {
      // 1. Add user message
      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text,
        timestamp: new Date(),
      };

      // 2. Create placeholder for assistant response
      const assistantId = `assistant-${Date.now()}`;
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsGenerating(true);

      try {
        // 3. Stream tokens from backend
        for await (const token of streamGenerate({
          prefix: text,
          max_length: 200,
        })) {
          if (token.error) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      content: `خرابی: ${token.error}`,
                      isStreaming: false,
                    }
                  : m
              )
            );
            break;
          }

          // Update the assistant message with each new token
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: token.full_text,
                    isStreaming: !token.is_finished,
                  }
                : m
            )
          );

          if (token.is_finished) break;
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "نامعلوم خرابی";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: `بیک اینڈ سے رابطہ نہیں ہو سکا: ${errorMessage}`,
                  isStreaming: false,
                }
              : m
          )
        );
      } finally {
        // Mark streaming as done
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, isStreaming: false } : m
          )
        );
        setIsGenerating(false);
      }
    },
    []
  );

  return (
    <main className="min-h-screen flex flex-col px-4 py-4 md:px-8 max-w-7xl mx-auto">
      {/* Header */}
      <Header />

      {/* Content */}
      <div className="flex-1 flex flex-col md:flex-row gap-4 mt-4">
        {/* Chat area (main column) */}
        <div className="flex-1 flex flex-col gap-4 order-2 md:order-1">
          <ChatWindow messages={messages} />
          <InputBar onSend={handleSend} isGenerating={isGenerating} />
        </div>

        {/* Sidebar (team members) */}
        <div className="w-full md:w-64 shrink-0 order-1 md:order-2">
          <TeamSidebar />
        </div>
      </div>

      {/* Footer accent */}
      <div className="mt-4 h-[1px] bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
    </main>
  );
}
