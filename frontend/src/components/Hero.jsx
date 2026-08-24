import React from "react";
import { motion } from "framer-motion";
import { ArrowUpRight, Sparkles } from "lucide-react";

const HERO_IMG =
  "https://images.unsplash.com/photo-1729006557274-d955ca21fe0c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjV8MHwxfHNlYXJjaHwzfHxhYnN0cmFjdCUyMGFyY2hpdGVjdHVyZSUyMGx1eHVyeSUyMGdvbGR8ZW58MHx8fHwxNzg3NjA0NDYyfDA&ixlib=rb-4.1.0&q=85";

export default function Hero() {
  return (
    <section id="top" data-testid="hero-section" className="relative pt-40 pb-24 md:pb-32 overflow-hidden">
      <div className="pointer-events-none absolute -top-40 -right-40 w-[720px] h-[720px] glow-gold blur-3xl" />
      <div className="pointer-events-none absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "linear-gradient(rgba(212,175,55,.5) 1px, transparent 1px), linear-gradient(90deg, rgba(212,175,55,.5) 1px, transparent 1px)", backgroundSize: "80px 80px" }} />

      <div className="max-w-[1400px] mx-auto px-6 md:px-12 grid grid-cols-12 gap-8 relative">
        {/* Left */}
        <div className="col-span-12 lg:col-span-7 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="flex items-center gap-3 mb-8"
          >
            <span className="w-8 h-px bg-gold" />
            <span className="h-eyebrow">Merton · KMV · Basel III</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.05 }}
            className="h-display text-[3.3rem] sm:text-[4.2rem] lg:text-[5.6rem]"
          >
            The gold standard
            <br />
            in <em className="rule-serif text-gold-light">credit intelligence.</em>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.15 }}
            className="mt-8 max-w-xl text-ivory/60 text-lg leading-relaxed font-light"
          >
            AURELIS is a market-implied, structural credit-risk engine trusted by
            private banks and next-generation fintechs. Distance-to-Default,
            Vasicek-Kealhofer, Altman Z, and ensemble ML — engineered for the
            institutions that write the world&rsquo;s largest cheques.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.25 }}
            className="mt-12 flex flex-wrap items-center gap-4"
          >
            <a href="#invitation" data-testid="hero-primary-cta" className="btn-primary inline-flex items-center gap-3">
              Request Private Demo
              <ArrowUpRight size={16} strokeWidth={1.5} />
            </a>
            <a href="#showcase" data-testid="hero-secondary-cta" className="btn-ghost inline-flex items-center gap-3">
              Explore the Platform
            </a>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.2, delay: 0.5 }}
            className="mt-16 flex items-center gap-6 text-ivory/40 text-xs tracking-[0.22em] uppercase"
          >
            <div className="flex items-center gap-2">
              <Sparkles size={14} className="text-gold" strokeWidth={1.25} />
              <span>By invitation only</span>
            </div>
            <span className="w-px h-4 bg-white/15" />
            <span>Est. 2026 · London · Zurich · Singapore</span>
          </motion.div>
        </div>

        {/* Right — architectural image */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.2, delay: 0.2 }}
          className="col-span-12 lg:col-span-5 relative"
        >
          <div className="relative aspect-[3/4] border border-white/10 overflow-hidden">
            <img
              src={HERO_IMG}
              alt="Gold architectural abstract"
              className="absolute inset-0 w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-onyx-950 via-onyx-950/30 to-transparent" />
            <div className="absolute bottom-6 left-6 right-6 flex items-end justify-between">
              <div>
                <p className="h-eyebrow">Series I · 2026</p>
                <p className="font-serif text-2xl mt-2 text-ivory/90">Aurelis Ledger</p>
              </div>
              <p className="font-serif italic text-gold-light text-sm">
                — «Pecunia intelligens.»
              </p>
            </div>
          </div>

          {/* Floating ticker card */}
          <div className="hidden md:block absolute -left-10 bottom-10 bg-onyx-900/90 backdrop-blur border border-gold/25 p-5 w-64 shadow-[0_0_40px_rgba(212,175,55,0.08)]">
            <div className="flex items-center justify-between text-[10px] tracking-[0.22em] uppercase text-ivory/50">
              <span>Live · PD (1y)</span>
              <span className="text-gold">●</span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="tick-value text-4xl text-ivory">0.42<span className="text-gold">%</span></span>
              <span className="text-xs text-emerald-400">−0.03</span>
            </div>
            <div className="mt-4 h-8 flex items-end gap-[3px]">
              {[6, 8, 5, 9, 12, 10, 14, 11, 15, 13, 17, 20, 18, 22].map((h, i) => (
                <span key={i} style={{ height: `${h * 3}%` }} className="w-full bg-gradient-to-t from-gold-dark to-gold-light opacity-80" />
              ))}
            </div>
            <p className="mt-3 text-[10px] text-ivory/40 tracking-widest uppercase">DD · 6.87σ · Investment grade</p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
