import React, { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";

const STATS = [
  { value: 4.2, prefix: "$", suffix: "T", label: "Assets Analysed" },
  { value: 98.7, suffix: "%", label: "Model AUC" },
  { value: 12480, label: "Counterparties Covered" },
  { value: 187, suffix: " days", label: "Lead Time vs. Agencies" },
];

function Count({ to, prefix = "", suffix = "", visible }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!visible) return;
    const start = performance.now();
    const dur = 1600;
    let raf;
    const tick = (t) => {
      const p = Math.min((t - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setN(to * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to, visible]);

  const isInt = Number.isInteger(to);
  const display = isInt ? Math.round(n).toLocaleString() : n.toFixed(1);
  return (
    <span>
      {prefix}
      {display}
      {suffix}
    </span>
  );
}

export default function MetricsBand() {
  const ref = useRef(null);
  const visible = useInView(ref, { once: true, margin: "-50px" });
  return (
    <section ref={ref} data-testid="metrics-band" className="py-24 md:py-28 border-y border-white/5 bg-onyx-950 relative">
      <div className="max-w-[1400px] mx-auto px-6 md:px-12 grid grid-cols-2 md:grid-cols-4 gap-10 md:gap-4">
        {STATS.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, delay: i * 0.08 }}
            className="text-center md:text-left"
          >
            <p className="tick-value text-5xl md:text-6xl text-ivory">
              <Count to={s.value} prefix={s.prefix} suffix={s.suffix} visible={visible} />
            </p>
            <div className="mt-4 h-px w-10 bg-gold mx-auto md:mx-0" />
            <p className="mt-4 h-eyebrow text-ivory/50">{s.label}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
