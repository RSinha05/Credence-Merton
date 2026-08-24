import React from "react";
import { ShieldCheck, Lock, Fingerprint, FileCheck2, Server, Landmark } from "lucide-react";

const BADGES = [
  { icon: ShieldCheck, label: "SOC 2 Type II" },
  { icon: FileCheck2, label: "ISO 27001" },
  { icon: Landmark, label: "Basel III Aligned" },
  { icon: Lock, label: "AES-256 · TLS 1.3" },
  { icon: Server, label: "Private Cloud & On-Prem" },
  { icon: Fingerprint, label: "IFRS 9 Ready" },
];

export default function Compliance() {
  return (
    <section id="compliance" data-testid="compliance-section" className="py-24 md:py-28 border-y border-white/5 bg-onyx-900/40">
      <div className="max-w-[1400px] mx-auto px-6 md:px-12">
        <div className="grid grid-cols-12 gap-10 items-end mb-14">
          <div className="col-span-12 lg:col-span-6">
            <p className="h-eyebrow">Assurance</p>
            <h2 className="h-display text-4xl lg:text-5xl mt-6">
              Engineered for those
              <br />
              who cannot afford <em className="rule-serif text-gold-light">imprecision.</em>
            </h2>
          </div>
          <p className="col-span-12 lg:col-span-5 lg:col-start-8 text-ivory/55 font-light leading-relaxed">
            AURELIS is deployed under the same governance regime as your core
            ledger. Every model artifact is versioned, every calculation
            reproducible, every access audit-trailed.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-px bg-white/5 border border-white/5">
          {BADGES.map((b) => (
            <div key={b.label} className="bg-onyx-950 p-6 flex flex-col items-center justify-center text-center gap-3">
              <b.icon size={22} strokeWidth={1.25} className="text-gold" />
              <p className="text-[0.72rem] tracking-[0.22em] uppercase text-ivory/70">{b.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
