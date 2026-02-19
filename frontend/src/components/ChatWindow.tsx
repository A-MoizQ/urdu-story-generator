"use client";

import { useEffect, useRef } from "react";
import { ChatMessage } from "@/lib/types";
import ChatBubble from "./ChatBubble";

interface ChatWindowProps {
  messages: ChatMessage[];
}

export default function ChatWindow({ messages }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="relative flex flex-col transition-colors duration-700" style={{ height: "500px" }}>

      {/* ── Mughal Palace arch frame top ── */}
      <div className="relative flex-shrink-0" style={{ zIndex: 10 }}>
        <svg
          viewBox="0 0 700 90"
          className="w-full"
          style={{ display: "block", marginBottom: "-2px" }}
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="archGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--arch-bg-top)" stopOpacity="1"/>
              <stop offset="100%" stopColor="var(--arch-bg-bot)" stopOpacity="1"/>
            </linearGradient>
          </defs>

          {/* Solid arch background */}
          <path
            d="M0,90 L0,50 Q10,20 30,10 Q80,0 130,2 Q200,-4 280,0 Q350,-6 420,0 Q500,-4 570,2 Q620,0 670,10 Q690,20 700,50 L700,90 Z"
            fill="url(#archGrad)"
            stroke="rgba(200,169,110,0.6)"
            strokeWidth="1.5"
          />
          {/* Inner arch relief */}
          <path
            d="M20,90 L20,55 Q28,28 50,18 Q100,6 150,8 Q220,2 280,6 Q350,0 420,6 Q480,2 550,8 Q600,6 650,18 Q672,28 680,55 L680,90"
            fill="none"
            stroke="rgba(200,169,110,0.25)"
            strokeWidth="1"
            strokeDasharray="6 4"
          />
          {/* Left pillar */}
          <rect x="0" y="0" width="22" height="90" fill="var(--arch-bg-bot)" stroke="rgba(200,169,110,0.4)" strokeWidth="1"/>
          <rect x="4" y="4" width="14" height="82" fill="none" stroke="rgba(200,169,110,0.2)" strokeWidth="0.5" strokeDasharray="3 3"/>
          {/* Right pillar */}
          <rect x="678" y="0" width="22" height="90" fill="var(--arch-bg-bot)" stroke="rgba(200,169,110,0.4)" strokeWidth="1"/>
          <rect x="682" y="4" width="14" height="82" fill="none" stroke="rgba(200,169,110,0.2)" strokeWidth="0.5" strokeDasharray="3 3"/>

          {/* Central finial / crest */}
          <polygon points="350,0 342,12 350,8 358,12" fill="#C8A96E" opacity="0.9"/>
          <circle cx="350" cy="0" r="5" fill="#C8A96E"/>
          <circle cx="350" cy="0" r="2.5" fill="#E8D4A0"/>

          {/* Floral medallion at arch keystone */}
          <circle cx="350" cy="30" r="14" fill="none" stroke="rgba(200,169,110,0.4)" strokeWidth="1"/>
          <circle cx="350" cy="30" r="8" fill="none" stroke="rgba(200,169,110,0.3)" strokeWidth="0.8"/>
          <circle cx="350" cy="30" r="3" fill="rgba(200,169,110,0.5)"/>
          {[0,45,90,135,180,225,270,315].map((angle, i) => {
            const r = 11;
            const rad = (angle * Math.PI) / 180;
            const x = 350 + r * Math.cos(rad);
            const y = 30 + r * Math.sin(rad);
            return <circle key={i} cx={x} cy={y} r="1.5" fill="rgba(200,169,110,0.5)"/>;
          })}

          {/* Left & right arch quarter-circle details */}
          <path d="M140,90 Q140,50 170,30" fill="none" stroke="rgba(200,169,110,0.2)" strokeWidth="0.8"/>
          <path d="M560,90 Q560,50 530,30" fill="none" stroke="rgba(200,169,110,0.2)" strokeWidth="0.8"/>
        </svg>
      </div>

      {/* ── Main chat body ── */}
      <div
        className="flex-1 flex flex-col overflow-hidden jali-overlay scan-line-overlay relative transition-colors duration-700"
        style={{
          background: "linear-gradient(180deg, var(--arch-card-bg) 0%, var(--bg-card) 60%, var(--arch-card-deep) 100%)",
          border: "2px solid var(--border-color)",
          borderTop: "none",
          boxShadow: "inset 0 0 40px rgba(0,0,0,0.1), 0 8px 30px rgba(0,0,0,0.2)",
        }}
      >
        {/* Messages scroll area */}
        <div className="relative z-10 flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <p className="urdu-text font-urdu text-lg animate-pulse transition-colors duration-700" style={{ color: "var(--text-muted)" }}>
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

      {/* ── Bottom arch sill ── */}
      <div
        className="flex-shrink-0 h-4 rounded-b-xl transition-colors duration-700"
        style={{
          background: "linear-gradient(180deg, var(--arch-bg-bot), var(--arch-bg-top))",
          border: "2px solid var(--border-color)",
          borderTop: "none",
          boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
        }}
      >
        <div className="flex justify-center gap-3 h-full items-center">
          {[...Array(9)].map((_, i) => (
            <div key={i} className="w-1 h-1 rounded-full opacity-50" style={{ background: "#C8A96E" }} />
          ))}
        </div>
      </div>
    </div>
  );
}
