"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type GoogleStatus = {
  connected: boolean;
  connected_email?: string;
  google_calendar_id?: string;
  updated_at?: string;
};

export default function SettingsPage() {
  const router = useRouter();

  const [status, setStatus] = useState<GoogleStatus | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadStatus() {
    const tenantId = localStorage.getItem("tenant_id");

    if (!tenantId) {
      router.push("/login");
      return;
    }

    const res = await fetch("/api/google/status", {
      headers: {
        "x-tenant-id": tenantId,
      },
      cache: "no-store",
    });

    const data = await res.json();
    setStatus(data);
    setLoading(false);
  }

  async function connectGoogle() {
    const tenantId = localStorage.getItem("tenant_id");

    if (!tenantId) {
      router.push("/login");
      return;
    }

    const res = await fetch("/api/google/connect", {
      headers: {
        "x-tenant-id": tenantId,
      },
      cache: "no-store",
    });

    const data = await res.json();

    if (data.authorization_url) {
      window.location.href = data.authorization_url;
    } else {
      alert("Google-Verbindung konnte nicht gestartet werden.");
    }
  }

  async function disconnectGoogle() {
    if (!confirm("Google Kalender wirklich trennen?")) return;

    const tenantId = localStorage.getItem("tenant_id");

    const res = await fetch("/api/google/disconnect", {
      method: "DELETE",
      headers: {
        "x-tenant-id": tenantId || "",
      },
    });

    if (res.ok) {
      await loadStatus();
    } else {
      alert("Google Kalender konnte nicht getrennt werden.");
    }
  }

  useEffect(() => {
    loadStatus();
  }, []);

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <button onClick={() => router.push("/")} style={backButton}>
          ← Zurück
        </button>

        <h1 style={{ fontSize: 34, marginBottom: 8 }}>Einstellungen</h1>

        <p style={{ color: "#94a3b8", marginBottom: 32 }}>
          Verbinde deinen Google Kalender, damit Termine automatisch erstellt und gelöscht werden können.
        </p>

        <section style={cardStyle}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 20 }}>
            <div>
              <h2 style={{ marginTop: 0 }}>Google Kalender</h2>

              {loading ? (
                <p style={{ color: "#94a3b8" }}>Lade Status...</p>
              ) : status?.connected ? (
                <>
                  <p style={{ color: "#22c55e", fontWeight: 700 }}>
                    ✅ Verbunden
                  </p>

                  <p style={infoText}>
                    Konto: <strong>{status.connected_email}</strong>
                  </p>

                  <p style={infoText}>
                    Kalender: <strong>{status.google_calendar_id}</strong>
                  </p>
                </>
              ) : (
                <>
                  <p style={{ color: "#facc15", fontWeight: 700 }}>
                    ⚠️ Nicht verbunden
                  </p>

                  <p style={infoText}>
                    Ohne Google-Verbindung können Termine nicht automatisch im Kalender erstellt werden.
                  </p>
                </>
              )}
            </div>

            <div>
              {status?.connected ? (
                <button onClick={disconnectGoogle} style={dangerButton}>
                  Verbindung trennen
                </button>
              ) : (
                <button onClick={connectGoogle} style={primaryButton}>
                  Google verbinden
                </button>
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

const pageStyle = {
  minHeight: "100vh",
  background:
    "radial-gradient(circle at top left, rgba(37,99,235,0.22), transparent 30%), #020617",
  color: "white",
  padding: "40px",
  fontFamily:
    "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Arial",
};

const containerStyle = {
  maxWidth: 900,
  margin: "0 auto",
};

const cardStyle = {
  background: "rgba(15, 23, 42, 0.92)",
  border: "1px solid #1e293b",
  borderRadius: 22,
  padding: 28,
  boxShadow: "0 20px 50px rgba(0,0,0,0.25)",
};

const infoText = {
  color: "#cbd5e1",
  lineHeight: 1.6,
};

const primaryButton = {
  background: "linear-gradient(135deg, #2563eb, #0ea5e9)",
  color: "white",
  border: "none",
  padding: "12px 18px",
  borderRadius: 12,
  cursor: "pointer",
  fontWeight: 800,
};

const dangerButton = {
  background: "#dc2626",
  color: "white",
  border: "none",
  padding: "12px 18px",
  borderRadius: 12,
  cursor: "pointer",
  fontWeight: 800,
};

const backButton = {
  background: "transparent",
  color: "#93c5fd",
  border: "none",
  cursor: "pointer",
  marginBottom: 24,
  fontSize: 15,
};