import React from "react";
import Marquee from "react-fast-marquee";

const NAMES = [
  "J.P. Morgan Private",
  "UBS Wealth",
  "Rothschild & Cie",
  "Goldman Sachs",
  "Pictet & Cie",
  "Lombard Odier",
  "HSBC Private",
  "Julius Bär",
  "Morgan Stanley",
  "Standard Chartered",
];

export default function TrustStrip() {
  return (
    <section data-testid="trust-strip" className="border-y border-white/10 bg-onyx-950 py-10">
      <div className="max-w-[1400px] mx-auto px-6 md:px-12 flex flex-col md:flex-row items-center gap-8">
        <p className="h-eyebrow shrink-0 text-ivory/50">Entrusted by</p>
        <div className="w-full overflow-hidden">
          <Marquee gradient gradientColor="#050505" gradientWidth={80} speed={30} pauseOnHover>
            {NAMES.concat(NAMES).map((n, i) => (
              <span key={i} className="logo-word mx-10">{n}</span>
            ))}
          </Marquee>
        </div>
      </div>
    </section>
  );
}
