"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const items = [
  { href: "/", label: "Sessions" },
  { href: "/how-it-works", label: "How It Works" },
  { href: "/quality", label: "Quality" },
  { href: "/methodology", label: "Methodology" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-20 border-b border-border-subtle bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-accent text-sm font-black text-white">A</span>
          <span className="text-sm font-bold tracking-tight">
            Adaptive Analyst Agent
            <span className="ml-2 hidden font-normal text-muted sm:inline">an AI data analyst that adapts to who&apos;s asking</span>
          </span>
        </Link>
        <nav className="ml-auto flex items-center gap-1 overflow-x-auto">
          {items.map((it) => {
            const active = it.href === "/" ? pathname === "/" : pathname.startsWith(it.href);
            return (
              <Link
                key={it.href}
                href={it.href}
                className={clsx(
                  "whitespace-nowrap rounded-md px-2.5 py-1.5 text-sm",
                  active ? "bg-accent-soft font-semibold text-accent" : "text-foreground/70 hover:bg-zinc-100 hover:text-foreground",
                )}
              >
                {it.label}
              </Link>
            );
          })}
        </nav>
        <span className="hidden shrink-0 rounded-full border border-amber-300 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-800 md:inline">
          Recorded real runs · synthetic data
        </span>
      </div>
    </header>
  );
}
