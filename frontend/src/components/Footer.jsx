import React from "react";

const YEAR = new Date().getFullYear();

const cols = [
  {
    title: "Platform",
    items: ["Distance-to-Default", "Portfolio Underwriting", "Regulatory Reporting", "APIs & Exports"],
  },
  {
    title: "Institution",
    items: ["Governance", "Security", "Compliance", "Client Committee"],
  },
  {
    title: "Correspondence",
    items: ["London — Threadneedle St.", "Zurich — Bahnhofstrasse", "Singapore — Raffles Place", "New York — Park Avenue"],
  },
];

export default function Footer() {
  return (
    <footer data-testid="site-footer" className="pt-24 pb-8 border-t border-white/5 bg-onyx-950 relative">
      <div className="max-w-[1400px] mx-auto px-6 md:px-12">
        <div className="grid grid-cols-12 gap-10 pb-16 border-b border-white/5">
          <div className="col-span-12 lg:col-span-4">
            <div className="flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-gold" />
              <span className="font-serif text-2xl tracking-[0.28em]">AURELIS</span>
            </div>
            <p className="mt-6 text-ivory/50 font-light max-w-sm leading-relaxed">
              A private credit-intelligence house serving investment banks,
              private wealth managers and next-generation fintechs.
            </p>
            <p className="mt-8 font-serif italic text-gold-light">
              «Pecunia intelligens.»
            </p>
          </div>

          {cols.map((c) => (
            <div key={c.title} className="col-span-6 md:col-span-4 lg:col-span-2">
              <p className="h-eyebrow text-ivory/60">{c.title}</p>
              <ul className="mt-6 space-y-3">
                {c.items.map((i) => (
                  <li key={i}>
                    <a href="#" className="link-sweep text-ivory/60 hover:text-ivory text-sm">
                      {i}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          <div className="col-span-12 lg:col-span-2">
            <p className="h-eyebrow text-ivory/60">Enquiries</p>
            <a href="mailto:committee@aurelis.credit" className="mt-6 inline-block link-sweep text-ivory">committee@aurelis.credit</a>
            <p className="mt-3 text-ivory/40 text-xs tracking-wider">Encrypted PGP on request</p>
          </div>
        </div>

        {/* Massive brand mark */}
        <div className="py-16 select-none overflow-hidden">
          <p className="font-serif text-[18vw] leading-[0.85] text-transparent bg-clip-text bg-gradient-to-b from-ivory/10 to-transparent tracking-[-0.02em]">
            AURELIS
          </p>
        </div>

        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 text-[0.72rem] tracking-widest uppercase text-ivory/40">
          <p>© {YEAR} Aurelis Ledger Ltd. All rights reserved.</p>
          <div className="flex flex-wrap gap-6">
            <a href="#" className="link-sweep">Terms</a>
            <a href="#" className="link-sweep">Privacy</a>
            <a href="#" className="link-sweep">Regulatory</a>
            <span>MSB · FCA notice on file</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
