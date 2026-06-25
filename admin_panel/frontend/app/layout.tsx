import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PromptCraftAI Admin",
  description: "Standalone admin panel for PromptCraftAI"
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
