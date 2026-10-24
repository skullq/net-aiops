import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Net-AIOps Studio | Cisco IOS-XE Causal AI Operations",
  description: "NetworkX Causal DiGraph, Scrapli IOS-XE MCP, and Real-time SSE Diagnostic Studio",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="dark">
      <body className="bg-slate-950 text-slate-100 h-screen w-screen overflow-hidden antialiased">
        {children}
      </body>
    </html>
  );
}
