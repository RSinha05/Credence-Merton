import React from "react";
import { motion } from "framer-motion";
import { Check } from "lucide-react";

const SHOWCASE_IMG =
  "https://images.unsplash.com/photo-1551288049-bebda4e38f71?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA3MDB8MHwxfHNlYXJjaHwxfHxmaW5hbmNpYWwlMjBkYXRhJTIwYW5hbHl0aWNzJTIwZGFzaGJvYXJkJTIwZGFya3xlbnwwfHx8fDE3ODc2MDQ0NjJ8MA&ixlib=rb-4.1.0&q=85";

const FEATURES = [
  "Vasicek-Kealhofer iteration with 5–10 pass convergence",
  "PD term structures at 0.5, 1, 2, 3 and 5 years",
  "Ensemble ML early-warning: XGBoost + DTW clustering",
  "GARCH(1,1) equity volatility forecasting",
  "Retail, corporate and multi-asset coverage",
  "REST API + streaming exports for downstream systems",
];

const SNAPSHOT = [
  { ticker: "MSFT", rating: "AAA", pd: "0.02%", dd: "9.12", trend: "steady" },
  { ticker: "JPM", rating: "A+", pd: "0.31%", dd: "6.44", trend: "up" },
  { ticker: "F", rating: "BBB−", pd: "1.87%", dd: "3.12", trend: "watch" },
  { ticker: "AAL", rating: "B+", pd: "6.42%", dd: "1.71", trend: "elevated" },
];

export default function Showcase() {
  return (
    <section id="showcase" data-testid="showcase-section" className="py-24 md:py-32 bg-onyx-900/40 border-y border-white/5">
      <div className="max-w-[1400px] mx-auto px-6 md:px-12 grid grid-cols-12 gap-10 items-center">
        {/* Left — image + snapshot */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.9 }}
          className="col-span-12 lg:col-span-7 relative"
        >
          <div className="relative border border-white/10 overflow-hidden aspect-[16/11]">
            <img src={SHOWCASE_IMG} alt="Analytics" className="absolute inset-0 w-full h-full object-cover opacity-70" />
            <div className="absolute inset-0 bg-gradient-to-tr from-onyx-950 via-onyx-950/40 to-transparent" />
          </div>

          <div className="hidden md:block absolute -right-6 -bottom-10 w-[380px] bg-onyx-950 border border-gold/25 p-6 shadow-[0_0_60px_rgba(212,175,55,0.08)]">
            <div className="flex items-center justify-between mb-4">
              <p className="h-eyebrow">Counterparty Snapshot</p>
              <span className="text-[10px] tracking-widest text-gold">LIVE</span>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-ivory/40 text-[10px] tracking-widest uppercase border-b border-white/10">
                  <th className="text-left py-2 font-normal">Ticker</th>
                  <th className="text-left font-normal">Rating</th>
                  <th className="text-right font-normal">PD 1y</th>
                  <th className="text-right font-normal">DD</th>
                </tr>
              </thead>
              <tbody>
                {SNAPSHOT.map((row) => (
                  <tr key={row.ticker} className="border-b border-white/5">
                    <td className="py-2.5 font-serif text-ivory">{row.ticker}</td>
                    <td className="text-ivory/70">{row.rating}</td>
                    <td className="text-right tick-value text-gold-light">{row.pd}</td>
                    <td className="text-right text-ivory/70 tabular-nums">{row.dd}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Right — copy + features */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.9 }}
          className="col-span-12 lg:col-span-5"
        >
          <p className="h-eyebrow">The Intelligence Layer</p>
          <h2 className="h-display text-4xl lg:text-5xl mt-6">
            A single pane
            <br />
            for <em className="rule-serif text-gold-light">every</em> exposure.
          </h2>
          <p className="mt-6 text-ivory/60 font-light leading-relaxed">
            From a single ticker to a book of thirty thousand. AURELIS ingests
            equity, EDGAR filings, sovereign rates and internal ledgers to
            produce the credit signal your rating desk actually needs — not
            weeks after the fact, but this morning.
          </p>

          <ul className="mt-10 space-y-4">
            {FEATURES.map((f) => (
              <li key={f} className="flex items-start gap-3 text-ivory/75 text-[0.95rem] leading-relaxed">
                <Check size={16} strokeWidth={1.5} className="text-gold mt-1 shrink-0" />
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </motion.div>
      </div>
    </section>
  );
}
