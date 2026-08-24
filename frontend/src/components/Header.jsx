import React, { useState, useEffect } from "react";

const links = [
  { href: "#pillars", label: "Platform" },
  { href: "#showcase", label: "Intelligence" },
  { href: "#methodology", label: "Methodology" },
  { href: "#compliance", label: "Assurance" },
];

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      data-testid="site-header"
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-500 ${
        scrolled
          ? "bg-onyx-950/85 backdrop-blur-xl border-b border-white/5"
          : "bg-transparent border-b border-transparent"
      }`}
    >
      <div className="max-w-[1400px] mx-auto px-6 md:px-12 flex items-center justify-between h-[76px]">
        <a href="#top" data-testid="brand-mark" className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-gold inline-block" />
          <span className="font-serif text-2xl tracking-[0.28em] text-ivory">
            AURELIS
          </span>
        </a>

        <nav className="hidden lg:flex items-center gap-10">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              data-testid={`nav-${l.label.toLowerCase()}`}
              className="link-sweep text-[0.78rem] tracking-[0.22em] uppercase text-ivory/70 hover:text-ivory transition-colors"
            >
              {l.label}
            </a>
          ))}
        </nav>

        <div className="hidden lg:flex items-center gap-6">
          <a
            href="#invitation"
            data-testid="header-cta"
            className="btn-primary"
          >
            Request Invitation
          </a>
        </div>

        <button
          onClick={() => setOpen((v) => !v)}
          data-testid="mobile-menu-toggle"
          className="lg:hidden text-ivory p-2"
          aria-label="Toggle menu"
        >
          <div className="w-6 flex flex-col gap-[5px]">
            <span className={`h-px bg-ivory transition-all ${open ? "translate-y-[6px] rotate-45" : ""}`} />
            <span className={`h-px bg-ivory transition-opacity ${open ? "opacity-0" : ""}`} />
            <span className={`h-px bg-ivory transition-all ${open ? "-translate-y-[6px] -rotate-45" : ""}`} />
          </div>
        </button>
      </div>

      {open && (
        <div className="lg:hidden border-t border-white/5 bg-onyx-950/95 backdrop-blur-xl">
          <div className="px-6 py-8 flex flex-col gap-6">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className="text-sm tracking-[0.22em] uppercase text-ivory/80"
              >
                {l.label}
              </a>
            ))}
            <a
              href="#invitation"
              onClick={() => setOpen(false)}
              className="btn-primary text-center"
            >
              Request Invitation
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
