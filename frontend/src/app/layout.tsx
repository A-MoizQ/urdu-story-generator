import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "مست اردو کہانیاں جنریٹر",
  description: "AI-powered Urdu story generator for children",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ur" dir="rtl">
      <body style={{ minHeight: "100vh" }}>{children}</body>
    </html>
  );
}
