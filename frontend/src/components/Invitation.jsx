import React, { useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { ArrowUpRight, Check } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AUM_OPTIONS = [
  "Under $500M",
  "$500M – $2B",
  "$2B – $10B",
  "$10B – $50B",
  "$50B – $250B",
  "$250B+",
];

export default function Invitation() {
  const [form, setForm] = useState({
    name: "",
    institution: "",
    email: "",
    role: "",
    aum_range: "",
    message: "",
  });
  const [status, setStatus] = useState({ state: "idle", error: null });

  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setStatus({ state: "loading", error: null });
    try {
      await axios.post(`${API}/demo-requests`, form);
      setStatus({ state: "success", error: null });
      setForm({ name: "", institution: "", email: "", role: "", aum_range: "", message: "" });
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        (Array.isArray(err?.response?.data) ? err.response.data[0]?.msg : null) ||
        "We could not deliver your request. Please retry in a moment.";
      setStatus({ state: "error", error: typeof detail === "string" ? detail : "Please review your entries." });
    }
  };

  return (
    <section id="invitation" data-testid="invitation-section" className="py-24 md:py-32 relative">
      <div className="pointer-events-none absolute inset-x-0 top-10 h-[520px] glow-gold blur-3xl opacity-70" />
      <div className="max-w-[1400px] mx-auto px-6 md:px-12 grid grid-cols-12 gap-12 relative">
        {/* Left — editorial copy */}
        <div className="col-span-12 lg:col-span-5">
          <p className="h-eyebrow">By Invitation</p>
          <h2 className="h-display text-4xl lg:text-5xl mt-6">
            Request a private <em className="rule-serif text-gold-light">audience</em>.
          </h2>
          <p className="mt-6 text-ivory/60 font-light leading-relaxed">
            AURELIS is deployed on a bespoke, invitation-only basis. Share a
            few particulars and a member of our client committee will respond
            within two business days — discreetly, and in your jurisdiction.
          </p>

          <div className="mt-12 space-y-6 text-ivory/70">
            {[
              "White-glove onboarding, no self-serve trials",
              "Dedicated quantitative liaison assigned per institution",
              "Non-disclosure by default, always mutual",
            ].map((t) => (
              <div key={t} className="flex items-start gap-3">
                <Check size={16} strokeWidth={1.5} className="text-gold mt-1 shrink-0" />
                <span className="font-light">{t}</span>
              </div>
            ))}
          </div>

          <div className="mt-14 pt-8 border-t border-white/10 text-ivory/40 text-xs tracking-widest uppercase">
            London · Zurich · Singapore · New York
          </div>
        </div>

        {/* Right — form */}
        <motion.form
          onSubmit={onSubmit}
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          data-testid="demo-request-form"
          className="col-span-12 lg:col-span-6 lg:col-start-7 border border-white/10 bg-onyx-900/50 backdrop-blur p-8 lg:p-12"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <label className="block">
              <span className="h-eyebrow text-ivory/50">Full Name</span>
              <input
                type="text"
                required
                value={form.name}
                onChange={update("name")}
                data-testid="input-name"
                className="field mt-2"
                placeholder="Alexandra Meridian"
              />
            </label>
            <label className="block">
              <span className="h-eyebrow text-ivory/50">Institution</span>
              <input
                type="text"
                required
                value={form.institution}
                onChange={update("institution")}
                data-testid="input-institution"
                className="field mt-2"
                placeholder="Meridian Private Bank"
              />
            </label>
            <label className="block">
              <span className="h-eyebrow text-ivory/50">Work Email</span>
              <input
                type="email"
                required
                value={form.email}
                onChange={update("email")}
                data-testid="input-email"
                className="field mt-2"
                placeholder="a.meridian@bank.com"
              />
            </label>
            <label className="block">
              <span className="h-eyebrow text-ivory/50">Role</span>
              <input
                type="text"
                value={form.role}
                onChange={update("role")}
                data-testid="input-role"
                className="field mt-2"
                placeholder="Head of Credit Risk"
              />
            </label>
            <label className="block md:col-span-2">
              <span className="h-eyebrow text-ivory/50">Assets Under Management</span>
              <select
                required
                value={form.aum_range}
                onChange={update("aum_range")}
                data-testid="input-aum"
                className="field mt-2"
              >
                <option value="" disabled>
                  Select range
                </option>
                {AUM_OPTIONS.map((o) => (
                  <option key={o} value={o}>
                    {o}
                  </option>
                ))}
              </select>
            </label>
            <label className="block md:col-span-2">
              <span className="h-eyebrow text-ivory/50">A Note (Optional)</span>
              <textarea
                rows={3}
                value={form.message}
                onChange={update("message")}
                data-testid="input-message"
                className="field mt-2 resize-none"
                placeholder="Universe of interest, deployment preferences, timing…"
              />
            </label>
          </div>

          <div className="mt-10 flex flex-col md:flex-row md:items-center gap-4">
            <button
              type="submit"
              disabled={status.state === "loading"}
              data-testid="submit-demo-request"
              className="btn-primary flex-1 flex items-center justify-center gap-3 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {status.state === "loading" ? "Submitting…" : "Request Invitation"}
              <ArrowUpRight size={16} strokeWidth={1.5} />
            </button>
            <p className="text-ivory/40 text-xs tracking-widest uppercase md:max-w-[220px]">
              Reviewed personally. No mailing list.
            </p>
          </div>

          {status.state === "success" && (
            <div
              data-testid="success-message"
              className="mt-8 border border-gold/40 bg-gold/5 px-6 py-4 text-ivory/85"
            >
              <p className="font-serif text-xl text-gold-light">Received with thanks.</p>
              <p className="text-sm text-ivory/60 mt-1">
                A member of our client committee will be in touch within two
                business days.
              </p>
            </div>
          )}
          {status.state === "error" && (
            <div
              data-testid="error-message"
              className="mt-8 border border-red-400/40 bg-red-500/5 px-6 py-4 text-red-200 text-sm"
            >
              {status.error}
            </div>
          )}
        </motion.form>
      </div>
    </section>
  );
}
