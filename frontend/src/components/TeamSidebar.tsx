"use client";

import { TEAM_MEMBERS } from "@/lib/types";

export default function TeamSidebar() {
  return (
    /* Outer palanquin wrapper – hover opens the blinds */
    <div className="palki-container relative select-none" tabIndex={0}>

      {/* ── Palanquin body ── */}
      <div
        className="relative rounded-b-2xl overflow-visible transition-colors duration-700"
        style={{
          background: "linear-gradient(180deg, var(--palki-bg1) 0%, var(--palki-bg2) 40%, var(--arch-card-bg) 100%)",
          border: "2px solid var(--border-color)",
          boxShadow:
            "0 0 24px rgba(200,169,110,0.12), inset 0 0 20px rgba(0,0,0,0.2), 0 8px 32px rgba(0,0,0,0.3)",
        }}
      >

        {/* ── Bulbous dome / onion arch top ── */}
        <div className="relative -top-[38px] left-0 right-0 flex justify-center pointer-events-none">
          {/* Dome SVG */}
          <svg
            viewBox="0 0 220 80"
            className="w-[90%] overflow-visible"
            style={{ filter: "drop-shadow(0 -4px 10px rgba(200,169,110,0.25))" }}
          >
            {/* Dome fill */}
            <path
              d="M10,78 C10,78 10,50 30,32 C50,14 80,4 110,4 C140,4 170,14 190,32 C210,50 210,78 210,78 Z"
              fill="url(#domeGrad)"
              stroke="rgba(200,169,110,0.6)"
              strokeWidth="1.5"
            />
            {/* Finial spire */}
            <line x1="110" y1="4" x2="110" y2="-10" stroke="#C8A96E" strokeWidth="1.5"/>
            <circle cx="110" cy="-12" r="4" fill="#C8A96E" />
            <circle cx="110" cy="-12" r="2" fill="#E8D4A0" />
            {/* Arch detail lines */}
            <path
              d="M30,78 C30,78 32,52 50,36 C68,20 88,12 110,12 C132,12 152,20 170,36 C188,52 190,78 190,78"
              fill="none"
              stroke="rgba(200,169,110,0.25)"
              strokeWidth="1"
              strokeDasharray="4 3"
            />
            {/* Corner minarets */}
            <rect x="2" y="40" width="12" height="40" rx="2" fill="var(--arch-bg-top)" stroke="rgba(200,169,110,0.5)" strokeWidth="1"/>
            <ellipse cx="8" cy="38" rx="8" ry="12" fill="var(--palki-bg1)" stroke="rgba(200,169,110,0.5)" strokeWidth="1"/>
            <circle cx="8" cy="26" r="3" fill="#C8A96E"/>
            <rect x="206" y="40" width="12" height="40" rx="2" fill="var(--arch-bg-top)" stroke="rgba(200,169,110,0.5)" strokeWidth="1"/>
            <ellipse cx="212" cy="38" rx="8" ry="12" fill="var(--palki-bg1)" stroke="rgba(200,169,110,0.5)" strokeWidth="1"/>
            <circle cx="212" cy="26" r="3" fill="#C8A96E"/>
            <defs>
              <linearGradient id="domeGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--arch-bg-top)"/>
                <stop offset="100%" stopColor="var(--arch-bg-bot)"/>
              </linearGradient>
            </defs>
          </svg>
        </div>

        {/* ── Blind curtain strips (the "chik" blinds) ── */}
        <div
          className="absolute inset-0 z-20 flex flex-col overflow-hidden rounded-b-2xl"
          style={{ pointerEvents: "none" }}
        >
          {Array.from({ length: 10 }).map((_, i) => (
            <div
              key={i}
              className="blind-slat flex-1 w-full"
              style={{
                background: i % 2 === 0
                  ? "var(--palki-slat-even)"
                  : "var(--palki-slat-odd)",
                borderBottom: "1px solid rgba(200,169,110,0.2)",
                transitionDelay: `${i * 30}ms`,
              }}
            />
          ))}
        </div>

        {/* ── Carrier poles ── */}
        <div className="absolute -left-5 top-1/2 -translate-y-1/2 w-5 h-4 rounded-l-full"
          style={{ background: "linear-gradient(90deg, #A07840, #C8A96E)", border: "1px solid #E8D4A0" }} />
        <div className="absolute -right-5 top-1/2 -translate-y-1/2 w-5 h-4 rounded-r-full"
          style={{ background: "linear-gradient(270deg, #A07840, #C8A96E)", border: "1px solid #E8D4A0" }} />

        {/* ── Content (revealed when blinds open) ── */}
        <div className="relative z-10 p-4 pt-2">
          {/* Title */}
          <h2
            className="text-lg font-bold urdu-text font-urdu neon-glow mb-3 text-center transition-colors duration-700"
            style={{ color: "var(--text-primary)" }}
          >
            گروہ کے لوگ
          </h2>

          {/* Gold divider */}
          <div className="mughal-divider mb-3" />

          <ul className="space-y-3">
            {TEAM_MEMBERS.map((member, idx) => (
              <li
                key={member.id}
                className="flex items-center gap-3 urdu-text font-urdu text-sm animate-fade-in"
                style={{ animationDelay: `${idx * 150}ms` }}
              >
                {/* Ornamental dot */}
                <span className="relative flex h-2.5 w-2.5 shrink-0">
                  <span
                    className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                    style={{ background: "var(--gold)" }}
                  />
                  <span
                    className="relative inline-flex rounded-full h-2.5 w-2.5"
                    style={{ background: "var(--gold)" }}
                  />
                </span>
                <span className="transition-colors duration-700" style={{ color: "var(--text-primary)" }}>
                  {member.id}-{member.name}
                </span>
              </li>
            ))}
          </ul>

          {/* Bottom ornament */}
          <div className="mughal-divider mt-3" />
          <p className="text-center text-[10px] tracking-widest mt-2 opacity-50 transition-colors duration-700" style={{ color: "var(--gold)" }}>
            ❖ دربار۔ کہانی ❖
          </p>
        </div>
      </div>

      {/* ── Hover hint label on top ── */}
      <div className="absolute -top-6 left-0 right-0 text-center pointer-events-none">
        <span
          className="text-[10px] tracking-widest opacity-40 transition-all duration-300"
          style={{ color: "var(--gold)" }}
        >
          ▲ پردہ اٹھائیں ▲
        </span>
      </div>
    </div>
  );
}
