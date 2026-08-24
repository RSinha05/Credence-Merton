import React from "react";
import { motion } from "framer-motion";

const STEPS = [
  {
    numeral: "I",
    title: "Ingest",
    body: "Equity market caps, SEC EDGAR filings, sovereign yield curves, and your internal ledger — cleaned and normalised on entry.",
  },
  {
    numeral: "II",
    title: "Solve",
    body: "Vasicek-Kealhofer iteration for σᵥ and V until convergence. Altman Z and ensemble ML models run in parallel for triangulation.",
  },
  {
    numeral: "III",
    title: "Deliver",
    body: "Distance-to-Default, PD term structure, and stage-transition matrices — through UI, API, or the reports your regulator already accepts.",
  },
];

export default function Methodology() {
  return (
    <section id="methodology" data-testid="methodology-section" className="py-24 md:py-32 relative">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-40 glow-gold opacity-40" />
      <div className="max-w-[1400px] mx-auto px-6 md:px-12 relative">
        <div className="grid grid-cols-12 gap-8 mb-16">
          <div className="col-span-12 lg:col-span-6">
            <p className="h-eyebrow">Methodology</p>
            <h2 className="h-display text-4xl sm:text-5xl lg:text-6xl mt-6">
              A three-movement <em className="rule-serif text-gold-light">concerto</em>
              <br />
              for credit risk.
            </h2>
          </div>
          <div className="col-span-12 lg:col-span-5 lg:col-start-8 text-ivory/60 font-light leading-relaxed">
            Merton (1974) at its heart. Refined by four decades of empirical
            research. Delivered with the polish your investment committee
            expects on the tenth floor.
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-white/5">
          {STEPS.map((s, i) => (
            <motion.div
              key={s.numeral}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: i * 0.1 }}
              className="bg-onyx-950 p-10 md:p-14 relative"
              data-testid={`method-${i + 1}`}
            >
              <div className="flex items-baseline gap-6">
                <span className="font-serif italic text-6xl text-gold/60">{s.numeral}</span>
                <div className="hairline flex-1" />
              </div>
              <h3 className="font-serif text-3xl text-ivory mt-8">{s.title}</h3>
              <p className="mt-5 text-ivory/55 font-light leading-relaxed">{s.body}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
