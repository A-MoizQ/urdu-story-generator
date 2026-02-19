"use client";

export default function Header() {
  return (
    <header className="relative py-6 text-center">
      {/* Top ornamental border */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-[1px]"
        style={{ background: "linear-gradient(to right, transparent, var(--gold), transparent)", opacity: 0.7 }}
      />

      {/* Decorative corner flourishes */}
      <span className="absolute top-2 left-4 text-2xl opacity-50 select-none" style={{ color: "var(--gold)" }}>❧</span>
      <span className="absolute top-2 right-4 text-2xl opacity-50 select-none" style={{ color: "var(--gold)", transform: "scaleX(-1)", display: "inline-block" }}>❧</span>

      <h1
        className="text-3xl md:text-4xl font-bold urdu-text font-urdu neon-glow transition-colors duration-700"
        style={{ color: "var(--text-primary)" }}
      >
        مست اردو کہانیاں جنریٹر
      </h1>

      {/* Subtitle ornament */}
      <div className="flex items-center justify-center gap-3 mt-2">
        <div className="h-[1px] w-16" style={{ background: "linear-gradient(to right, transparent, var(--gold))" }} />
        <span className="text-[11px] opacity-60 tracking-widest uppercase select-none transition-colors duration-700" style={{ color: "var(--gold)" }}>
          ✦ دربارِ سخن ✦
        </span>
        <div className="h-[1px] w-16" style={{ background: "linear-gradient(to left, transparent, var(--gold))" }} />
      </div>

      {/* Bottom accent line */}
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1/2 h-[1px]"
        style={{ background: "linear-gradient(to right, transparent, var(--border-color), transparent)", opacity: 0.7 }}
      />
    </header>
  );
}
