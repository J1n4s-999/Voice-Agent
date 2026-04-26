"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        setError("Benutzername oder Passwort ist falsch.");
        return;
      }

      localStorage.setItem("tenant_id", data.tenant_id);
      localStorage.setItem("username", data.username);

      router.push("/");
    } catch {
      setError("Login fehlgeschlagen. Bitte erneut versuchen.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at top left, #1d4ed8 0, transparent 32%), linear-gradient(135deg, #020617 0%, #0f172a 55%, #111827 100%)",
        color: "#fff",
        fontFamily:
          "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Arial",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <section
        style={{
          width: "100%",
          maxWidth: 420,
          background: "rgba(15, 23, 42, 0.82)",
          border: "1px solid rgba(148, 163, 184, 0.25)",
          borderRadius: 24,
          padding: 32,
          boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
          backdropFilter: "blur(18px)",
        }}
      >
        <div style={{ marginBottom: 28 }}>
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: 16,
              background: "linear-gradient(135deg, #2563eb, #38bdf8)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 26,
              marginBottom: 18,
            }}
          >
            📅
          </div>

          <h1 style={{ fontSize: 30, margin: 0, letterSpacing: "-0.04em" }}>
            Admin Login
          </h1>

          <p style={{ color: "#94a3b8", marginTop: 8, lineHeight: 1.5 }}>
            Melde dich an, um Termine, Buchungen und Kundendaten zu verwalten.
          </p>
        </div>

        <form onSubmit={handleLogin}>
          <label style={label}>Benutzername</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="z. B. admin"
            autoComplete="username"
            style={input}
          />

          <label style={label}>Passwort</label>
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            type="password"
            autoComplete="current-password"
            style={input}
          />

          {error && (
            <div
              style={{
                background: "rgba(239, 68, 68, 0.12)",
                color: "#fca5a5",
                border: "1px solid rgba(248, 113, 113, 0.35)",
                borderRadius: 12,
                padding: "10px 12px",
                marginBottom: 16,
                fontSize: 14,
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "13px 16px",
              borderRadius: 14,
              border: "none",
              background: loading
                ? "#334155"
                : "linear-gradient(135deg, #2563eb, #0ea5e9)",
              color: "#fff",
              fontWeight: 800,
              fontSize: 15,
              cursor: loading ? "not-allowed" : "pointer",
              boxShadow: "0 14px 30px rgba(37, 99, 235, 0.28)",
            }}
          >
            {loading ? "Einloggen..." : "Einloggen"}
          </button>
        </form>

        <p
          style={{
            color: "#64748b",
            fontSize: 12,
            textAlign: "center",
            marginTop: 22,
          }}
        >
          Voice-Agent Dashboard · CDM Marketing
        </p>
      </section>
    </main>
  );
}

const label = {
  display: "block",
  color: "#cbd5e1",
  fontSize: 14,
  fontWeight: 700,
  marginBottom: 8,
};

const input = {
  width: "100%",
  padding: "13px 14px",
  borderRadius: 14,
  border: "1px solid rgba(148, 163, 184, 0.28)",
  background: "rgba(2, 6, 23, 0.58)",
  color: "#fff",
  outline: "none",
  marginBottom: 16,
  fontSize: 15,
};