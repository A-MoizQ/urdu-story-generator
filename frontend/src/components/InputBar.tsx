"use client";

import { useState, useRef, useEffect } from "react";

interface InputBarProps {
  onSend: (text: string) => void;
  isGenerating: boolean;
}

export default function InputBar({ onSend, isGenerating }: InputBarProps) {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isGenerating) {
      inputRef.current?.focus();
    }
  }, [isGenerating]);

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || isGenerating) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div
      className="flex gap-3 items-center px-3 py-3 rounded-xl transition-colors duration-700"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border-color)",
        boxShadow: "0 2px 16px rgba(0,0,0,0.15), inset 0 1px 0 rgba(200,169,110,0.06)",
      }}
    >
      {/* Generate button */}
      <button
        onClick={handleSubmit}
        disabled={!text.trim() || isGenerating}
        className="btn-generate rounded-xl px-6 py-3 font-bold urdu-text font-urdu text-base shrink-0"
        style={{ color: "var(--bubble-ai-txt)" }}
      >
        {isGenerating ? (
          <span className="flex items-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <span>جاری ہے...</span>
          </span>
        ) : (
          "جنریٹ کریں"
        )}
      </button>

      {/* Input field */}
      <div className="flex-1 relative">
        {/* Top-left ornament */}
        <span className="absolute top-1 left-2 text-[10px] opacity-25 pointer-events-none select-none" style={{ color: "var(--gold)" }}>✦</span>

        <input
          ref={inputRef}
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isGenerating}
          placeholder="ایک دفعہ ..."
          className="w-full rounded-xl px-5 py-3 urdu-text font-urdu text-base outline-none transition-all duration-300 disabled:opacity-50"
          dir="rtl"
          style={{
            background: "var(--input-bg)",
            border: "1px solid var(--input-border)",
            color: "var(--input-color)",
            caretColor: "var(--gold)",
          }}
          onFocus={(e) => {
            e.currentTarget.style.border = "1px solid var(--border-color)";
            e.currentTarget.style.boxShadow = "0 0 12px rgba(200,169,110,0.12)";
          }}
          onBlur={(e) => {
            e.currentTarget.style.border = "1px solid var(--input-border)";
            e.currentTarget.style.boxShadow = "none";
          }}
        />

        {/* Bottom-right ornament */}
        <span className="absolute bottom-1 right-2 text-[10px] opacity-25 pointer-events-none select-none" style={{ color: "var(--gold)" }}>✦</span>
      </div>
    </div>
  );
}
