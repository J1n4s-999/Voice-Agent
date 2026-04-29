"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Tenant = {
  id: string;
  name: string;
  agent_key: string;
};

export default function TenantsPage() {
  const router = useRouter();

  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [name, setName] = useState("");
  const [agentKey, setAgentKey] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    const role = localStorage.getItem("role");

    if (role !== "super_admin") {
      router.push("/");
      return;
    }

    loadTenants();
  }, [router]);

  async function loadTenants() {
    try {
      setLoading(true);
      setError("");

      const res = await fetch("/api/tenants", {
        cache: "no-store",
      });

      const data = await res.json();

      if (!res.ok) {
        setTenants([]);
        setError(data?.detail || data?.error || "Kunden konnten nicht geladen werden.");
        return;
      }

      if (Array.isArray(data)) {
        setTenants(data);
      } else if (Array.isArray(data.tenants)) {
        setTenants(data.tenants);
      } else {
        setTenants([]);
        setError("Die API hat kein gültiges Kunden-Array zurückgegeben.");
      }
    } catch (err) {
      console.error(err);
      setTenants([]);
      setError("Fehler beim Laden der Kunden.");
    } finally {
      setLoading(false);
    }
  }

  function openTenant(tenant: Tenant) {
    localStorage.setItem("tenant_id", tenant.id);
    localStorage.setItem("tenant_name", tenant.name);
    router.push("/");
  }

  async function createTenant() {
    if (!name || !agentKey || !username || !password) {
      alert("Bitte alle Felder ausfüllen.");
      return;
    }

    const res = await fetch("/api/tenants", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name,
        agent_key: agentKey,
        username,
        password,
      }),
    });

    const data = await res.json();

    if (!res.ok || !data.ok) {
      alert(data?.detail || data?.error || "Fehler beim Erstellen des Kunden.");
      return;
    }

    setName("");
    setAgentKey("");
    setUsername("");
    setPassword("");

    await loadTenants();
  }

  function logout() {
    localStorage.removeItem("tenant_id");
    localStorage.removeItem("tenant_name");
    localStorage.removeItem("username");
    localStorage.removeItem("role");

    router.push("/login");
  }

  if (loading) {
    return <main style={pageStyle}>Lade Kunden...</main>;
  }

  return (
    <main style={pageStyle}>
      <div style={headerStyle}>
        <div>
          <h1 style={{ margin: 0 }}>Kundenübersicht</h1>
          <p style={{ color: "#94a3b8" }}>
            Verwalte Kunden, Agent Keys und Kunden-Logins.
          </p>
        </div>

        <button onClick={logout} style={logoutButton}>
          Logout
        </button>
      </div>

      {error && <div style={errorBox}>{error}</div>}

      <section style={formCard}>
        <h2 style={{ marginTop: 0 }}>Neuen Kunden erstellen</h2>

        <div style={gridStyle}>
          <input
            placeholder="Kundenname"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={inputStyle}
          />

          <input
            placeholder="Agent Key"
            value={agentKey}
            onChange={(e) => setAgentKey(e.target.value)}
            style={inputStyle}
          />

          <input
            placeholder="Admin Benutzername"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={inputStyle}
          />

          <input
            placeholder="Admin Passwort"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={inputStyle}
          />
        </div>

        <button onClick={createTenant} style={primaryButton}>
          Kunde erstellen
        </button>
      </section>

      <section>
        <h2>Kunden</h2>

        {tenants.length === 0 && !error && (
          <p style={{ color: "#94a3b8" }}>Noch keine Kunden vorhanden.</p>
        )}

        <div style={tenantGrid}>
          {tenants.map((tenant) => (
            <div
              key={tenant.id}
              onClick={() => openTenant(tenant)}
              style={tenantCard}
            >
              <h3 style={{ marginTop: 0 }}>{tenant.name}</h3>
              <p style={{ color: "#94a3b8" }}>
                Agent Key: {tenant.agent_key}
              </p>
              <strong>Dashboard öffnen →</strong>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

const pageStyle: React.CSSProperties = {
  minHeight: "100vh",
  background:
    "radial-gradient(circle at top left, rgba(37,99,235,0.22), transparent 30%), #020617",
  color: "white",
  padding: "40px",
  fontFamily:
    "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Arial",
};

const headerStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: 30,
};

const formCard: React.CSSProperties = {
  background: "rgba(15, 23, 42, 0.9)",
  padding: 24,
  borderRadius: 20,
  marginBottom: 34,
  border: "1px solid #1e293b",
  boxShadow: "0 20px 50px rgba(0,0,0,0.25)",
};

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 12,
  marginBottom: 16,
};

const tenantGrid: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
  gap: 20,
};

const tenantCard: React.CSSProperties = {
  background: "rgba(15, 23, 42, 0.92)",
  padding: 24,
  borderRadius: 20,
  cursor: "pointer",
  border: "1px solid #1e293b",
  transition: "transform 0.15s ease, border-color 0.15s ease",
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "12px 14px",
  borderRadius: 12,
  border: "1px solid #334155",
  background: "#020617",
  color: "white",
  outline: "none",
  fontSize: 14,
};

const primaryButton: React.CSSProperties = {
  padding: "12px 18px",
  background: "linear-gradient(135deg, #2563eb, #0ea5e9)",
  color: "white",
  border: "none",
  borderRadius: 12,
  cursor: "pointer",
  fontWeight: 800,
};

const logoutButton: React.CSSProperties = {
  padding: "10px 16px",
  background: "#ef4444",
  color: "white",
  border: "none",
  borderRadius: 10,
  cursor: "pointer",
  fontWeight: 700,
};

const errorBox: React.CSSProperties = {
  background: "rgba(239, 68, 68, 0.15)",
  border: "1px solid rgba(239, 68, 68, 0.5)",
  color: "#fecaca",
  padding: 14,
  borderRadius: 14,
  marginBottom: 20,
};