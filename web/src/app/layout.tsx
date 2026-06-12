import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/nav";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Adaptive Analyst Agent — an AI data analyst that adapts to who's asking",
  description:
    "Portfolio demo: an LLM agent that writes and runs SQL and Python against a GTM warehouse, tailoring its analysis to Executive, Marketing, Sales, or Product stakeholders. Watch unedited recordings of real runs.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <Nav />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
        <footer className="border-t border-border-subtle bg-white">
          <div className="mx-auto max-w-6xl space-y-2 px-4 py-6 text-xs text-muted">
            <p>Independent portfolio project by Philip Felix.</p>
            <p>
              Every session shown is an unedited transcript of a real agent run (Claude API tool use against a
              read-only DuckDB warehouse of seeded synthetic GTM data). Nothing is mocked; errors and retries are
              part of the recordings. The agent runs live locally — see Methodology.{" "}
              <a href="https://github.com/pfelix828/context-agent" className="underline decoration-dotted underline-offset-2 hover:text-foreground">
                Code on GitHub
              </a>
              .
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
