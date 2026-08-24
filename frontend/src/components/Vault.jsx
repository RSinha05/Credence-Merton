import React, { useEffect, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { Lock, Download, ArrowUpRight, X, KeyRound } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const TOKEN_KEY = "aurelis_vault_grant";

function loadGrant() {
  try {
    const raw = localStorage.getItem(TOKEN_KEY);
    if (!raw) return null;
    const g = JSON.parse(raw);
    if (new Date(g.expires_at) < new Date()) {
      localStorage.removeItem(TOKEN_KEY);
      return null;
    }
    return g;
  } catch {
    return null;
  }
}

export default function Vault() {
  const [cases, setCases] = useState([]);
  const [grant, setGrant] = useState(loadGrant());
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ name: "", institution: "", email: "" });
  const [status, setStatus] = useState({ state: "idle", error: null });

  useEffect(() => {
    axios
      .get(`${API}/vault/case-studies`)
      .then((r) => setCases(r.data))
      .catch(() => setCases([]));
  }, []);

  const openVault = () => {
    setStatus({ state: "idle", error: null });
    setModalOpen(true);
  };

  const closeModal = () => setModalOpen(false);

  const onVerify = async (e) => {
    e.preventDefault();
    setStatus({ state: "loading", error: null });
    try {
      const { data } = await axios.post(`${API}/vault/verify`, form);
      localStorage.setItem(TOKEN_KEY, JSON.stringify(data));
      setGrant(data);
      setStatus({ state: "success", error: null });
      setTimeout(() => setModalOpen(false), 900);
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        "We could not verify those particulars. Please retry.";
      setStatus({
        state: "error",
        error: typeof detail === "string" ? detail : "Please review your entries.",
      });
    }
  };

  const revoke = () => {
    localStorage.removeItem(TOKEN_KEY);
    setGrant(null);
  };

  const download = (id) => {
    if (!grant) return;
    const url = `${API}/vault/download/${id}?token=${encodeURIComponent(grant.token)}`;
    window.open(url, "_blank");
  };

  return (
    <section id="vault" data-testid="vault-section" className="py-24 md:py-32 border-t border-white/5 relative">
      <div className="pointer-events-none absolute -left-40 top-40 w-[520px] h-[520px] glow-gold blur-3xl opacity-70" />
      <div className="max-w-[1400px] mx-auto px-6 md:px-12 relative">
        <div className="grid grid-cols-12 gap-10 items-end mb-14">
          <div className="col-span-12 lg:col-span-7">
            <p className="h-eyebrow">Case Study Vault</p>
            <h2 className="h-display text-4xl sm:text-5xl lg:text-6xl mt-6">
              A private library,
              <br />
              opened by <em className="rule-serif text-gold-light">institution.</em>
            </h2>
          </div>
          <div className="col-span-12 lg:col-span-5 text-ivory/60 font-light leading-relaxed">
            Four dossiers on record. Access is granted only to a verified
            corporate address; each download is watermarked to the recipient
            institution and expires after seven days.
          </div>
        </div>

        {/* Access strip */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border border-white/10 bg-onyx-900/50 px-6 md:px-8 py-5 mb-10">
          <div className="flex items-center gap-4">
            <KeyRound size={18} strokeWidth={1.25} className="text-gold" />
            {grant ? (
              <div>
                <p className="text-ivory text-sm">
                  Vault open <span className="text-ivory/40">·</span>{" "}
                  <span data-testid="vault-institution" className="text-gold-light">{grant.institution}</span>
                </p>
                <p className="text-ivory/40 text-xs tracking-widest uppercase mt-1">
                  Expires {new Date(grant.expires_at).toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" })}
                </p>
              </div>
            ) : (
              <p className="text-ivory/70 text-sm">
                Restricted archive <span className="text-ivory/30">·</span> Corporate email required
              </p>
            )}
          </div>
          {grant ? (
            <button onClick={revoke} data-testid="vault-revoke" className="btn-ghost text-[0.7rem]">
              Close Vault
            </button>
          ) : (
            <button onClick={openVault} data-testid="vault-open-cta" className="btn-primary inline-flex items-center gap-3">
              Request Access
              <ArrowUpRight size={16} strokeWidth={1.5} />
            </button>
          )}
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-white/5 border border-white/5">
          {cases.map((c, i) => (
            <motion.article
              key={c.id}
              data-testid={`vault-card-${c.id}`}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: i * 0.07 }}
              className="bg-onyx-950 p-10 lg:p-12 relative group"
            >
              <div className="flex items-start justify-between mb-8">
                <span className="font-serif text-gold/60 text-xl tracking-widest">{c.kicker}</span>
                <span className={`inline-flex items-center gap-2 px-3 py-1 border text-[0.65rem] tracking-widest uppercase ${grant ? "border-gold/40 text-gold-light" : "border-white/15 text-ivory/50"}`}>
                  {grant ? "Access granted" : <><Lock size={11} strokeWidth={1.5} /> Restricted</>}
                </span>
              </div>
              <h3 className="font-serif text-2xl lg:text-3xl text-ivory">{c.title}</h3>
              <p className="mt-2 h-eyebrow text-ivory/50">{c.sector} · {c.year} · {c.pages} pages</p>
              <p className="mt-6 text-ivory/55 font-light leading-relaxed">{c.summary}</p>

              <div className="mt-8 flex items-center gap-4">
                {grant ? (
                  <button
                    onClick={() => download(c.id)}
                    data-testid={`vault-download-${c.id}`}
                    className="inline-flex items-center gap-3 text-gold-light hover:text-gold text-[0.72rem] tracking-[0.22em] uppercase link-sweep"
                  >
                    <Download size={14} strokeWidth={1.5} /> Download PDF
                  </button>
                ) : (
                  <button
                    onClick={openVault}
                    data-testid={`vault-locked-${c.id}`}
                    className="inline-flex items-center gap-3 text-ivory/50 hover:text-ivory text-[0.72rem] tracking-[0.22em] uppercase link-sweep"
                  >
                    <Lock size={14} strokeWidth={1.5} /> Request access
                  </button>
                )}
              </div>

              <div className="absolute left-0 right-0 bottom-0 h-px bg-gold origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-700" />
            </motion.article>
          ))}
        </div>
      </div>

      {/* Modal */}
      {modalOpen && (
        <div data-testid="vault-modal" className="fixed inset-0 z-[80] flex items-center justify-center bg-onyx-950/85 backdrop-blur-md px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="relative w-full max-w-lg border border-gold/25 bg-onyx-900 p-8 lg:p-10 shadow-[0_0_80px_rgba(212,175,55,0.12)]"
          >
            <button onClick={closeModal} data-testid="vault-modal-close" aria-label="Close" className="absolute top-4 right-4 text-ivory/50 hover:text-ivory">
              <X size={18} strokeWidth={1.25} />
            </button>
            <p className="h-eyebrow">Vault Verification</p>
            <h3 className="font-serif text-3xl mt-4 text-ivory">Kindly identify yourself.</h3>
            <p className="mt-3 text-ivory/55 text-sm leading-relaxed">
              Access is granted for seven days and watermarked to your
              institution. Corporate or institutional email required.
            </p>

            <form onSubmit={onVerify} className="mt-8 space-y-6" data-testid="vault-form">
              <label className="block">
                <span className="h-eyebrow text-ivory/50">Full Name</span>
                <input required minLength={2} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="field mt-2" placeholder="Alexandra Meridian" data-testid="vault-input-name" />
              </label>
              <label className="block">
                <span className="h-eyebrow text-ivory/50">Institution</span>
                <input required minLength={2} value={form.institution} onChange={(e) => setForm({ ...form, institution: e.target.value })} className="field mt-2" placeholder="Meridian Private Bank" data-testid="vault-input-institution" />
              </label>
              <label className="block">
                <span className="h-eyebrow text-ivory/50">Corporate Email</span>
                <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="field mt-2" placeholder="a.meridian@bank.com" data-testid="vault-input-email" />
              </label>

              <button
                type="submit"
                disabled={status.state === "loading" || status.state === "success"}
                data-testid="vault-submit"
                className="btn-primary w-full inline-flex items-center justify-center gap-3 disabled:opacity-60"
              >
                {status.state === "loading" ? "Verifying…" : status.state === "success" ? "Access Granted" : "Open the Vault"}
                {status.state !== "loading" && <ArrowUpRight size={16} strokeWidth={1.5} />}
              </button>

              {status.state === "error" && (
                <p data-testid="vault-error" className="border border-red-400/40 bg-red-500/5 px-4 py-3 text-red-200 text-sm">
                  {status.error}
                </p>
              )}
            </form>
          </motion.div>
        </div>
      )}
    </section>
  );
}
