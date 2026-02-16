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
    <div className="flex gap-3 items-center">
      {/* Generate button */}
      <button
        onClick={handleSubmit}
        disabled={!text.trim() || isGenerating}
        className="btn-generate rounded-xl px-6 py-3 text-surface font-bold urdu-text font-urdu text-base shrink-0"
      >
        {isGenerating ? (
          <span className="flex items-center gap-2">
            <svg
              className="animate-spin h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            <span>جاری ہے...</span>
          </span>
        ) : (
          "جنریٹ کریں"
        )}
      </button>

      {/* Input field */}
      <div className="flex-1 relative">
        <input
          ref={inputRef}
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isGenerating}
          placeholder="ایک دفعہ ..."
          className="w-full bg-surface-light neon-border-cyan rounded-xl px-5 py-3 urdu-text font-urdu text-base text-gray-100 placeholder-gray-500 outline-none focus:ring-2 focus:ring-accent-cyan/30 transition-all duration-300 disabled:opacity-50"
          dir="rtl"
        />

        {/* Decorative corner accents */}
        <div className="absolute top-0 right-0 w-3 h-3 border-t border-r border-accent-cyan/40 rounded-tr-xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-3 h-3 border-b border-l border-accent-cyan/40 rounded-bl-xl pointer-events-none" />
      </div>
    </div>
  );
}
