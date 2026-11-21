"use client";

import { useEffect, useState } from "react";

type ApiStatus = {
  api: string;
  stage: number;
  database_configured: boolean;
  legal_corpus_ready: boolean;
  answer_engine_ready: boolean;
  message: string;
};

export default function Home() {
  const [status, setStatus] = useState<ApiStatus | null>(null);
  const [question, setQuestion] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetch(`${apiUrl}/api/status`)
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => setStatus(null));
  }, [apiUrl]);

  async function submitQuestion(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setNotice("");
    try {
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
      });
      const data = await response.json();
      setNotice(data.detail || "The API responded.");
    } catch {
      setNotice("Cannot reach the backend. Check that Docker services are running.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Irish Law AI home">
          <span className="brandMark">§</span>
          <span>Irish Law AI</span>
        </a>
        <span className="topTag">RESEARCH PREVIEW · STAGE 1</span>
      </header>

      <section className="hero">
        <div className="eyebrow"><span className="pulse" /> BUILT AROUND IRISH LEGISLATION</div>
        <h1>Understand Irish law.<br /><em>With the sources attached.</em></h1>
        <p className="intro">
          A legal research assistant designed to explain Irish legislation in plain English
          and show the statutory provisions behind every answer.
        </p>

        <div className="statusCard">
          <div className="statusHead">
            <strong>Development system status</strong>
            <span className={status?.api === "online" ? "statusPill online" : "statusPill"}>
              {status?.api === "online" ? "API ONLINE" : "CHECKING API"}
            </span>
          </div>
          <div className="statusGrid">
            <div><span>Backend API</span><b>{status?.api === "online" ? "Connected" : "Not connected"}</b></div>
            <div><span>Database config</span><b>{status ? (status.database_configured ? "Configured" : "Missing") : "Checking…"}</b></div>
            <div><span>Irish law corpus</span><b>{status?.legal_corpus_ready ? "Ready" : "Not imported yet"}</b></div>
            <div><span>Answer engine</span><b>{status?.answer_engine_ready ? "Ready" : "Not enabled yet"}</b></div>
          </div>
        </div>

        <section className="chatCard">
          <div className="chatTitle">
            <div>
              <span className="miniLabel">TRY THE INTERFACE</span>
              <h2>Ask an Irish law question</h2>
            </div>
            <span className="lockIcon">§</span>
          </div>
          <form onSubmit={submitQuestion}>
            <label className="srOnly" htmlFor="question">Your legal question</label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. What notice must a landlord give before ending a tenancy?"
              rows={3}
            />
            <button type="submit" disabled={loading || !question.trim()}>
              {loading ? "Checking…" : "Send question"} <span>→</span>
            </button>
          </form>
          {notice && <div className="notice" role="status">{notice}</div>}
          <p className="disclaimer">
            The legal answer engine is intentionally disabled in this first setup stage.
            Do not use this preview for legal decisions.
          </p>
        </section>
      </section>

      <section className="featureRow">
        <div><span>01</span><strong>Official sources</strong><p>Build on Irish legislation, not model memory.</p></div>
        <div><span>02</span><strong>Provision-level search</strong><p>Retrieve the sections relevant to each question.</p></div>
        <div><span>03</span><strong>Visible citations</strong><p>Show the legal text and its source alongside explanations.</p></div>
      </section>
      <footer>Independent research tool · Not a solicitor · Not legal advice</footer>
    </main>
  );
}
