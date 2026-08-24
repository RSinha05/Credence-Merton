import React from "react";
import { motion } from "framer-motion";

const PORTRAIT_1 =
  "https://images.unsplash.com/photo-1560250097-0b93528c311a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2ODh8MHwxfHNlYXJjaHwxfHxleGVjdXRpdmUlMjBwb3J0cmFpdCUyMHByb2Zlc3Npb25hbHxlbnwwfHx8fDE3ODc2MDQ0NjJ8MA&ixlib=rb-4.1.0&q=85";
const PORTRAIT_2 =
  "https://images.pexels.com/photos/27086922/pexels-photo-27086922.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940";

const QUOTES = [
  {
    q: "AURELIS gave our credit committee a market-implied signal that led every downgrade by a full quarter. It is, quite simply, the instrument we should have built ourselves.",
    name: "Alexandra M.",
    role: "Head of Credit, Continental Private Bank",
    img: PORTRAIT_1,
  },
  {
    q: "The Merton engine is faithful to the mathematics; the delivery is faithful to how we actually work. Rare combination.",
    name: "Daniel R.",
    role: "Co-Founder, Neobank (Series C)",
    img: PORTRAIT_2,
  },
];

export default function Testimonials() {
  return (
    <section data-testid="testimonials-section" className="py-24 md:py-32">
      <div className="max-w-[1400px] mx-auto px-6 md:px-12">
        <div className="mb-16 max-w-2xl">
          <p className="h-eyebrow">Discreet Voices</p>
          <h2 className="h-display text-4xl lg:text-5xl mt-6">
            What our <em className="rule-serif text-gold-light">principals</em> say.
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          {QUOTES.map((t, i) => (
            <motion.figure
              key={t.name}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: i * 0.1 }}
              className="relative border border-white/8 p-10 lg:p-14 bg-onyx-900/40"
              data-testid={`testimonial-${i + 1}`}
            >
              <div className="absolute -top-6 left-10 font-serif text-gold text-8xl leading-none select-none">&ldquo;</div>
              <blockquote className="font-serif text-2xl lg:text-3xl leading-[1.35] font-light text-ivory/90">
                {t.q}
              </blockquote>
              <figcaption className="mt-10 flex items-center gap-5">
                <img
                  src={t.img}
                  alt={t.name}
                  className="w-14 h-14 object-cover grayscale contrast-125 border border-gold/40"
                />
                <div>
                  <p className="text-ivory">{t.name}</p>
                  <p className="text-ivory/50 text-sm tracking-wider">{t.role}</p>
                </div>
              </figcaption>
            </motion.figure>
          ))}
        </div>
      </div>
    </section>
  );
}
