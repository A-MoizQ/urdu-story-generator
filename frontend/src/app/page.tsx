"use client";

import { useState, useCallback, useEffect } from "react";
import Header from "@/components/Header";
import TeamSidebar from "@/components/TeamSidebar";
import ChatWindow from "@/components/ChatWindow";
import InputBar from "@/components/InputBar";
import { ChatMessage, SYSTEM_GREETING } from "@/lib/types";
import { streamGenerate } from "@/lib/api";

/* ─── tiny helper: generate star positions once ─── */
function generateStars(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    top: `${Math.random() * 100}%`,
    left: `${Math.random() * 100}%`,
    size: Math.random() * 2.5 + 1,
    delay: `${Math.random() * 4}s`,
    duration: `${1.5 + Math.random() * 3}s`,
  }));
}

const STARS = generateStars(180);
const SUN_RAYS = 16; // number of sun rays

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([SYSTEM_GREETING]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isNight, setIsNight] = useState(false);

  // Sync night-mode class to <body> so the full viewport background changes
  useEffect(() => {
    if (isNight) {
      document.body.classList.add("night-mode");
    } else {
      document.body.classList.remove("night-mode");
    }
  }, [isNight]);
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
                  ? { ...m, content: `خرابی: ${token.error}`, isStreaming: false }
                  : m
              )
            );
            break;
          }

          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: token.full_text, isStreaming: !token.is_finished }
                : m
            )
          );

          if (token.is_finished) break;
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "نامعلوم خرابی";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: `بیک اینڈ سے رابطہ نہیں ہو سکا: ${errorMessage}`, isStreaming: false }
              : m
          )
        );
      } finally {
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, isStreaming: false } : m))
        );
        setIsGenerating(false);
      }
    },
    []
  );

  return (
    <main
      className={`min-h-screen flex flex-col px-4 py-4 md:px-8 max-w-7xl mx-auto relative overflow-hidden transition-all duration-1000 ${isNight ? "night-mode" : ""}`}
      style={{ background: "var(--bg-page)" }}
    >

      {/* ════════════════════════════════════════
          STARS (shown only at night)
      ════════════════════════════════════════ */}
      {isNight && (
        <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
          {STARS.map((star) => (
            <div
              key={star.id}
              className="absolute rounded-full"
              style={{
                top: star.top,
                left: star.left,
                width: `${star.size}px`,
                height: `${star.size}px`,
                background: star.size > 2.8 ? "#E8D4A0" : "#ffffff",
                boxShadow: star.size > 2.5 ? `0 0 ${star.size * 3}px rgba(232,212,160,0.8)` : "none",
                animation: `starTwinkle ${star.duration} ease-in-out ${star.delay} infinite`,
              }}
            />
          ))}
          {/* Shooting star streaks */}
          {[...Array(3)].map((_, i) => (
            <div
              key={`shoot-${i}`}
              className="absolute rounded-full opacity-0"
              style={{
                top: `${10 + i * 25}%`,
                left: "-2%",
                width: "80px",
                height: "2px",
                background: "linear-gradient(90deg, rgba(232,212,160,0) 0%, rgba(232,212,160,0.8) 100%)",
                animation: `shootingStar 6s ease-in ${i * 2.5}s infinite`,
              }}
            />
          ))}
        </div>
      )}

      {/* ════════════════════════════════════════
          SUN / MOON + RAYS
      ════════════════════════════════════════ */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 flex flex-col items-center" style={{ zIndex: 5, pointerEvents: "none" }}>
        {/* Celestial rays radiating outward */}
        <div
          className="absolute"
          style={{ top: "30px", left: "50%", width: 0, height: 0, pointerEvents: "none" }}
        >
          {Array.from({ length: SUN_RAYS }).map((_, i) => {
            const angle = (i / SUN_RAYS) * 360;
            const len = 200 + (i % 3) * 60;
            return (
              <div
                key={i}
                className="absolute"
                style={{
                  width: "2px",
                  height: `${len}px`,
                  background: isNight
                    ? `linear-gradient(to bottom, rgba(155,176,208,${0.3 - (i % 4) * 0.05}), transparent)`
                    : `linear-gradient(to bottom, rgba(200,169,110,${0.55 - (i % 4) * 0.08}), transparent)`,
                  transformOrigin: "top center",
                  transform: `rotate(${angle}deg)`,
                  left: "-1px",
                  top: "0",
                  animation: `rayPulse ${2.5 + (i % 3) * 0.5}s ease-in-out ${(i * 0.15) % 2}s infinite`,
                }}
              />
            );
          })}
        </div>
      </div>

      {/* ════════════════════════════════════════
          SUN / MOON BUTTON
      ════════════════════════════════════════ */}
      <div className="relative flex justify-center mb-2" style={{ zIndex: 20 }}>
        <button
          onClick={() => setIsNight((n) => !n)}
          className="relative flex items-center justify-center rounded-full transition-all duration-700 focus:outline-none"
          style={{
            width: "72px",
            height: "72px",
            background: isNight
              ? "radial-gradient(circle at 35% 35%, #E8F0FF, #9BB0D0 50%, #6080B0)"
              : "radial-gradient(circle at 35% 35%, #FFF5CC, #E8D4A0 45%, #C8A96E 80%)",
            boxShadow: isNight
              ? "0 0 20px rgba(155,176,208,0.6), 0 0 50px rgba(96,128,176,0.3)"
              : "0 0 25px rgba(200,169,110,0.8), 0 0 60px rgba(200,169,110,0.4), 0 0 100px rgba(200,169,110,0.2)",
            animation: isNight ? "moonGlow 3s ease-in-out infinite" : "sunGlow 3s ease-in-out infinite",
            cursor: "pointer",
          }}
          title={isNight ? "چاند — دن کے لیے کلک کریں" : "سورج — رات کے لیے کلک کریں"}
          aria-label="Toggle day/night"
        >
          {isNight ? (
            <svg viewBox="0 0 40 40" className="w-9 h-9">
              <defs>
                <radialGradient id="moonFill" cx="40%" cy="35%">
                  <stop offset="0%" stopColor="#E8F0FF"/>
                  <stop offset="100%" stopColor="#7090B8"/>
                </radialGradient>
              </defs>
              <circle cx="20" cy="20" r="18" fill="url(#moonFill)"/>
              <circle cx="26" cy="14" r="13" fill="#6080B0"/>
              <circle cx="12" cy="24" r="2" fill="rgba(155,176,208,0.4)"/>
              <circle cx="18" cy="30" r="1.5" fill="rgba(155,176,208,0.3)"/>
              <circle cx="9" cy="16" r="1" fill="rgba(155,176,208,0.4)"/>
              <text x="32" y="10" fontSize="6" fill="#E8D4A0" opacity="0.8">✦</text>
              <text x="2" y="12" fontSize="4" fill="#E8D4A0" opacity="0.6">✦</text>
            </svg>
          ) : (
            <svg viewBox="0 0 40 40" className="w-9 h-9" style={{ animation: "sunRotate 20s linear infinite" }}>
              <defs>
                <radialGradient id="sunFill" cx="40%" cy="38%">
                  <stop offset="0%" stopColor="#FFFACC"/>
                  <stop offset="60%" stopColor="#E8D4A0"/>
                  <stop offset="100%" stopColor="#C8A96E"/>
                </radialGradient>
              </defs>
              {Array.from({ length: 12 }).map((_, i) => {
                const a = (i / 12) * 360;
                const r1 = 17, r2 = 20;
                const ra = (a * Math.PI) / 180;
                const rb = ((a + 15) * Math.PI) / 180;
                const x1 = 20 + r1 * Math.cos(ra);
                const y1 = 20 + r1 * Math.sin(ra);
                const x2 = 20 + r2 * Math.cos(rb);
                const y2 = 20 + r2 * Math.sin(rb);
                return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="rgba(200,169,110,0.7)" strokeWidth="1.5"/>;
              })}
              <circle cx="20" cy="20" r="15" fill="url(#sunFill)"/>
              <circle cx="20" cy="20" r="10" fill="none" stroke="rgba(200,169,110,0.4)" strokeWidth="0.8"/>
              <circle cx="20" cy="20" r="5" fill="rgba(255,250,200,0.5)"/>
            </svg>
          )}
        </button>

        {/* Radiant halo ring */}
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 rounded-full pointer-events-none"
          style={{
            width: "72px",
            height: "72px",
            border: `2px solid ${isNight ? "rgba(155,176,208,0.3)" : "rgba(200,169,110,0.4)"}`,
            boxShadow: isNight ? "0 0 30px rgba(155,176,208,0.2)" : "0 0 30px rgba(200,169,110,0.3)",
            animation: "floatAnim 4s ease-in-out infinite",
          }}
        />
      </div>

      {/* ════════════════════════════════════════
          HEADER
      ════════════════════════════════════════ */}
      <div className="relative" style={{ zIndex: 10 }}>
        <Header />
      </div>

      {/* ════════════════════════════════════════
          CONTENT GRID
      ════════════════════════════════════════ */}
      <div className="flex-1 flex flex-col md:flex-row gap-6 mt-4 relative" style={{ zIndex: 10 }}>
        <div className="flex-1 flex flex-col gap-4 order-2 md:order-1">
          <ChatWindow messages={messages} />
          <InputBar onSend={handleSend} isGenerating={isGenerating} />
        </div>
        <div className="w-full md:w-64 shrink-0 order-1 md:order-2 relative" style={{ paddingTop: "2.5rem" }}>
          <TeamSidebar />
        </div>
      </div>

      {/* ════════════════════════════════════════
          FOOTER ORNAMENT
      ════════════════════════════════════════ */}
      <div className="relative mt-6" style={{ zIndex: 10 }}>
        <div className="mughal-divider" />
        <p className="text-center text-[10px] tracking-widest mt-2 opacity-40" style={{ color: "var(--gold)" }}>
          ✦ دارالسلطنت ✦ داستانِ دل ✦
        </p>
      </div>

      {/* ════════════════════════════════════════
          Jali background overlay
      ════════════════════════════════════════ */}
      <div
        className="fixed inset-0 pointer-events-none transition-opacity duration-1000"
        style={{
          zIndex: 1,
          opacity: isNight ? 0.4 : 1,
          backgroundImage: `
            repeating-linear-gradient(0deg, transparent, transparent 38px, rgba(200,169,110,0.025) 38px, rgba(200,169,110,0.025) 39px),
            repeating-linear-gradient(90deg, transparent, transparent 38px, rgba(200,169,110,0.025) 38px, rgba(200,169,110,0.025) 39px),
            repeating-linear-gradient(45deg, transparent, transparent 27px, rgba(200,169,110,0.015) 27px, rgba(200,169,110,0.015) 28px),
            repeating-linear-gradient(-45deg, transparent, transparent 27px, rgba(200,169,110,0.015) 27px, rgba(200,169,110,0.015) 28px)
          `,
        }}
      />

      {/* CSS for shooting stars & misc animations */}
      <style>{`
        @keyframes shootingStar {
          0%   { transform: translateX(0)   translateY(0); opacity: 0; }
          5%   { opacity: 0.8; }
          50%  { transform: translateX(110vw) translateY(30vh); opacity: 0; }
          100% { transform: translateX(110vw) translateY(30vh); opacity: 0; }
        }
        @keyframes floatAnim {
          0%, 100% { transform: translate(-50%, 0px); }
          50%       { transform: translate(-50%, -5px); }
        }
        @keyframes moonGlow {
          0%, 100% { box-shadow: 0 0 20px rgba(155,176,208,0.5), 0 0 50px rgba(96,128,176,0.25); }
          50%       { box-shadow: 0 0 35px rgba(155,176,208,0.8), 0 0 80px rgba(96,128,176,0.45); }
        }
        @keyframes sunGlow {
          0%, 100% { box-shadow: 0 0 25px rgba(200,169,110,0.8), 0 0 60px rgba(200,169,110,0.4); }
          50%       { box-shadow: 0 0 40px rgba(232,212,160,1),   0 0 100px rgba(200,169,110,0.6); }
        }
        @keyframes sunRotate {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @keyframes rayPulse {
          0%, 100% { opacity: 0.45; transform: scaleY(1); }
          50%       { opacity: 0.85; transform: scaleY(1.07); }
        }
        @keyframes starTwinkle {
          0%, 100% { opacity: 0.2;  transform: scale(1);   }
          50%       { opacity: 1;    transform: scale(1.4); }
        }
      `}</style>
    </main>
  );
}

