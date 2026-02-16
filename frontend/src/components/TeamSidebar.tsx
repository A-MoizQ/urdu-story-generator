"use client";

import { TEAM_MEMBERS } from "@/lib/types";

export default function TeamSidebar() {
  return (
    <aside className="neon-border rounded-xl p-4 bg-surface-card backdrop-blur-sm">
      <h2 className="text-xl font-bold urdu-text font-urdu text-primary mb-4 neon-glow">
        گروہ کے لوگ
      </h2>

      <ul className="space-y-3">
        {TEAM_MEMBERS.map((member, idx) => (
          <li
            key={member.id}
            className="flex items-center gap-3 urdu-text font-urdu text-sm animate-fade-in"
            style={{ animationDelay: `${idx * 150}ms` }}
          >
            {/* Status dot */}
            <span className="relative flex h-2.5 w-2.5 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary" />
            </span>

            <span className="text-gray-200">
              {member.id}-{member.name}
            </span>
          </li>
        ))}
      </ul>
    </aside>
  );
}
