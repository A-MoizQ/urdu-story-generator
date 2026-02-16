"use client";

export default function Header() {
  return (
    <header className="relative py-4 text-center">
      {/* Top accent line */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-[1px] bg-gradient-to-r from-transparent via-primary to-transparent" />

      <h1 className="text-3xl md:text-4xl font-bold urdu-text font-urdu neon-glow text-primary">
        مست اردو کہانیاں جنریٹر
      </h1>

      {/* Bottom accent line */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1/2 h-[1px] bg-gradient-to-r from-transparent via-accent-cyan to-transparent" />
    </header>
  );
}
