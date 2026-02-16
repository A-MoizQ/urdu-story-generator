export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export interface TeamMember {
  name: string;
  id: number;
}

export const TEAM_MEMBERS: TeamMember[] = [
  { id: 1, name: "عبدالمعزقاضی" },
  { id: 2, name: "عبداللّٰہ بن منصور" },
  { id: 3, name: "امل خان" },
];

export const SYSTEM_GREETING: ChatMessage = {
  id: "system-greeting",
  role: "assistant",
  content:
    "جی ہاں! میں آپ کی اردو کہانی لکھنے میں مدد کر سکتا ہوں۔ آپ کس موضوع پر کہانی چاہتے ہیں؟",
  timestamp: new Date(),
};
