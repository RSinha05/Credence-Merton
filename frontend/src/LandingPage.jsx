import React, { useEffect } from "react";
import Lenis from "@studio-freight/lenis";
import "./App.css";
import Header from "./components/Header";
import Hero from "./components/Hero";
import TrustStrip from "./components/TrustStrip";
import Pillars from "./components/Pillars";
import Showcase from "./components/Showcase";
import Methodology from "./components/Methodology";
import MetricsBand from "./components/MetricsBand";
import Testimonials from "./components/Testimonials";
import Compliance from "./components/Compliance";
import Vault from "./components/Vault";
import Invitation from "./components/Invitation";
import Footer from "./components/Footer";

export default function App() {
  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.15,
      smoothWheel: true,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    });
    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);
    return () => lenis.destroy();
  }, []);

  return (
    <div className="noise relative min-h-screen bg-onyx-950 text-ivory">
      <Header />
      <main>
        <Hero />
        <TrustStrip />
        <Pillars />
        <Showcase />
        <Methodology />
        <MetricsBand />
        <Testimonials />
        <Compliance />
        <Vault />
        <Invitation />
      </main>
      <Footer />
    </div>
  );
}
