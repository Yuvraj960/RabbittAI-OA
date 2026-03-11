"use client";

import { useState, useCallback, DragEvent, ChangeEvent } from "react";

type Status = "idle" | "loading" | "success" | "error";

interface Step {
  id: string;
  label: string;
}

const STEPS: Step[] = [
  { id: "upload", label: "Parsing & validating your data file..." },
  { id: "ai", label: "Generating AI executive summary..." },
  { id: "email", label: "Sending report to your inbox..." },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");
  const [dragging, setDragging] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);

  const handleFileDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) validateAndSetFile(dropped);
  }, []);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) validateAndSetFile(selected);
  };

  const validateAndSetFile = (f: File) => {
    const ext = f.name.split(".").pop()?.toLowerCase();
    if (!["csv", "xlsx", "xls"].includes(ext || "")) {
      setStatus("error");
      setMessage("Only .csv, .xlsx, or .xls files are accepted.");
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      setStatus("error");
      setMessage("File must be smaller than 10MB.");
      return;
    }
    setFile(f);
    if (status === "error") {
      setStatus("idle");
      setMessage("");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !email) return;

    setStatus("loading");
    setMessage("");
    setCurrentStep(0);

    // Simulate step progression for UX feedback
    const stepTimers = [
      setTimeout(() => setCurrentStep(1), 2000),
      setTimeout(() => setCurrentStep(2), 5000),
    ];

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("email", email);

      const res = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        headers: {
          "X-API-Key": API_KEY,
        },
        body: formData,
      });

      stepTimers.forEach(clearTimeout);

      const data = await res.json();

      if (res.ok && data.success) {
        setCurrentStep(3);
        setStatus("success");
        setMessage(data.message);
      } else {
        setStatus("error");
        setMessage(data.detail || data.message || "Something went wrong. Please try again.");
        setCurrentStep(-1);
      }
    } catch {
      stepTimers.forEach(clearTimeout);
      setStatus("error");
      setMessage("Could not reach the server. Please check your connection and try again.");
      setCurrentStep(-1);
    }
  };

  const handleReset = () => {
    setFile(null);
    setEmail("");
    setStatus("idle");
    setMessage("");
    setCurrentStep(-1);
  };

  const isLoading = status === "loading";
  const canSubmit = !!file && email.includes("@") && !isLoading;

  return (
    <>
      <div className="bg-mesh" />
      <div className="bg-grid" />

      <main className="page">
        {/* ── Header ── */}
        <header className="header">
          <div className="logo">
            <div className="logo-icon">🐇</div>
            <span className="logo-text">
              Rabbitt<span className="logo-dot"> AI</span>
            </span>
          </div>
          <h1>
            Sales Insight<br />
            <span>Automator</span>
          </h1>
          <p>
            Upload your sales data and receive an AI-generated executive
            summary delivered directly to your inbox — in seconds.
          </p>
          <div className="badge-row">
            <span className="badge badge-accent">⚡ Gemini 2.5 Flash</span>
            <span className="badge badge-blue">📊 CSV &amp; XLSX</span>
            <span className="badge badge-green">✉️ Instant Delivery</span>
          </div>
        </header>

        {/* ── Card ── */}
        <div className="card">
          {status !== "success" ? (
            <form onSubmit={handleSubmit}>
              {/* Drop Zone */}
              <div
                className={`dropzone${dragging ? " active" : ""}${file ? " has-file" : ""}`}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleFileDrop}
              >
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileChange}
                  disabled={isLoading}
                  aria-label="Upload sales data file"
                />
                {file ? (
                  <>
                    <span className="drop-icon">✅</span>
                    <p className="drop-title">File ready!</p>
                    <div className="file-chip">
                      <span>📄</span>
                      <span className="file-chip-name">{file.name}</span>
                      <span style={{ color: "var(--text-muted)", marginLeft: 4 }}>
                        ({(file.size / 1024).toFixed(0)} KB)
                      </span>
                    </div>
                  </>
                ) : (
                  <>
                    <span className="drop-icon">📂</span>
                    <p className="drop-title">Drop your file here</p>
                    <p className="drop-subtitle">
                      or click to browse &mdash; .csv, .xlsx, .xls &nbsp;|&nbsp; max 10MB
                    </p>
                  </>
                )}
              </div>

              {/* Email Input */}
              <div className="form-group">
                <label className="form-label" htmlFor="email-input">
                  <span>✉️</span> Recipient Email
                </label>
                <input
                  id="email-input"
                  type="email"
                  className="form-input"
                  placeholder="executive@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isLoading}
                  required
                  aria-describedby="email-hint"
                />
              </div>

              {/* Loading steps */}
              {isLoading && (
                <div className="progress-steps" aria-live="polite">
                  {STEPS.map((step, idx) => (
                    <div
                      key={step.id}
                      className={`step ${
                        currentStep === idx
                          ? "active"
                          : currentStep > idx
                          ? "done"
                          : ""
                      }`}
                    >
                      <div className="step-dot" />
                      {currentStep > idx ? "✓ " : ""}
                      {step.label}
                    </div>
                  ))}
                </div>
              )}

              {/* Error */}
              {status === "error" && (
                <div className="alert alert-error" role="alert">
                  <span className="alert-icon">❌</span>
                  <div className="alert-content">
                    <p className="alert-title">Something went wrong</p>
                    <p className="alert-message">{message}</p>
                  </div>
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                className="btn-submit"
                disabled={!canSubmit}
                id="analyze-btn"
              >
                <span className="btn-inner">
                  {isLoading ? (
                    <>
                      <span className="spinner" aria-hidden="true" />
                      Analyzing…
                    </>
                  ) : (
                    <>
                      <span>🚀</span>
                      Generate &amp; Send Report
                    </>
                  )}
                </span>
              </button>
            </form>
          ) : (
            /* ── Success State ── */
            <div style={{ textAlign: "center", padding: "12px 0" }}>
              <div style={{ fontSize: 56, marginBottom: 20 }}>🎉</div>
              <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 12, color: "var(--text-primary)" }}>
                Report delivered!
              </h2>
              <div className="alert alert-success" style={{ textAlign: "left" }}>
                <span className="alert-icon">✅</span>
                <div className="alert-content">
                  <p className="alert-title">Success</p>
                  <p className="alert-message">{message}</p>
                </div>
              </div>
              <button
                className="btn-submit"
                onClick={handleReset}
                style={{ marginTop: 28 }}
                id="analyze-another-btn"
              >
                <span className="btn-inner">
                  <span>🔄</span> Analyze Another File
                </span>
              </button>
            </div>
          )}
        </div>

        {/* ── Footer ── */}
        <footer className="footer">
          <p>Powered by Google Gemini · Built by Rabbitt AI Engineering</p>
          <div style={{ marginTop: 12, display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <a
              href={`${API_URL}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="swagger-link"
            >
              📖 Swagger API Docs
            </a>
            <a
              href={`${API_URL}/api/health`}
              target="_blank"
              rel="noopener noreferrer"
              className="swagger-link"
            >
              💚 API Health
            </a>
          </div>
        </footer>
      </main>
    </>
  );
}
