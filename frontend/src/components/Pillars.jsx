import React from "react";
import { motion } from "framer-motion";
import { LineChart, ShieldCheck, Landmark, Scale } from "lucide-react";

const PILLARS = [
  {
    icon: LineChart,
    kicker: "01",
    title: "Distance-to-Default Engine",
    body: "A production-grade Merton/KMV solver — equity treated as a call on firm assets, iterated via Vasicek-Kealhofer until σᵥ converges. Market-implied PDs that move six-to-twelve months ahead of the agencies.",
  },
  {
    icon: Scale,
    kicker: "02",
    title: "Portfolio Underwriting",
    body: "From single-name to full book. Altman Z, ensemble ML early-warning, PD term structures at 0.5–5 years. Bespoke overlays for corporate, retail, and multi-asset universes.",
  },
  {
    icon: Landmark,
    kicker: "03",
    title: "Regulatory Reporting",
    body: "Basel III IRB-aligned outputs, IFRS 9 stage-transition matrices, and a full audit trail. Configurable for FCA, FINMA, MAS, HKMA, and RBI jurisdictions.",
  },
  {
    icon: ShieldCheck,
    kicker: "04",
    title: "Sovereign-Tier Security",
    body: "Isolated tenancy, end-to-end encryption, SOC 2 Type II and ISO 27001 aligned. On-premise, private cloud, or air-gapped deployment on request.",
  },
];

export default function Pillars() {
  return (
    <section id="pillars" data-testid="pillars-section" className="py-24 md:py-32 relative">
      <div className="max-w-[1400px] mx-auto px-6 md:px-12">
        <div className="grid grid-cols-12 gap-10 items-end mb-16">
          <div className="col-span-12 lg:col-span-6">
            <p className="h-eyebrow">The Platform</p>
            <h2 className="h-display text-4xl sm:text-5xl lg:text-6xl mt-6">
              Four pillars.
              <br />
              One <em className="rule-serif text-gold-light">unassailable</em> ledger.
            </h2>
          </div>
          <div className="col-span-12 lg:col-span-5 lg:col-start-8">
            <p className="text-ivory/60 font-light leading-relaxed">
              AURELIS is not a dashboard. It is a private, quant-grade
              infrastructure — engineered around the models your credit
              committees already trust, delivered with the discretion your
              clients expect.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-white/5 border border-white/5">
          {PILLARS.map((p, i) => (
            <motion.article
              key={p.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.7, delay: i * 0.08 }}
              className="bg-onyx-950 p-10 lg:p-14 group hover:bg-onyx-900 transition-colors relative"
              data-testid={`pillar-${i + 1}`}
            >
              <div className="flex items-start justify-between mb-10">
                <p.icon size={28} strokeWidth={1.25} className="text-gold" />
                <span className="font-serif text-gold/50 text-lg tracking-widest">{p.kicker}</span>
              </div>
              <h3 className="font-serif text-3xl font-light text-ivory mb-4">{p.title}</h3>
              <p className="text-ivory/55 font-light leading-relaxed">{p.body}</p>
              <div className="absolute left-0 right-0 bottom-0 h-px bg-gold origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-700" />
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
