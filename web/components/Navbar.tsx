"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Detect", icon: "🔍" },
  { href: "/analytics", label: "Analytics", icon: "📊" },
  { href: "/history", label: "History", icon: "🕐" },
  { href: "/legal", label: "Legal AI", icon: "⚖️" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link href="/" className="navbar-brand" style={{ textDecoration: "none" }}>
          <span>🚦</span>
          <div>
            <div style={{ lineHeight: 1.1 }}>GRiD Traffic AI</div>
            <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 400 }}>
              Flipkart GRiD — Theme 3
            </div>
          </div>
        </Link>

        <div className="navbar-links">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`navbar-link ${pathname === link.href ? "active" : ""}`}
            >
              {link.icon} {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
