import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "The System — Awakening",
  description: "Real actions become verifiable RPG progression.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
