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
    const res = await fetch("/api/tenants", {
      cache: "no-store",
    });

    const data = await res.json();

    setTenants(data);
    setLoading(false);
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
      alert("Fehler beim Erstellen des Kunden.");
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
    return (
      <main style={pageStyle}>
        <p>Lade Kunden...</p>
      </main>
    );
  }

  return (
    <main style={pageStyle}>
      <div style={headerStyle}>
        <div>
          <h1 style={{ fontSize: 34, margin: 0 }}>Kundenübersicht</h1>
          <p style={{ color: "#94a3b8", marginTop: 8 }}>
            Verwalte Kunden, Agent Keys und Kunden-Logins.
          </p>
        </div>

        <button onClick={logout} style={logoutButton}>
          Logout
        </button>
      </div>

      <section style={formCard}>
        <h2 style={{ marginTop: 0, marginBottom: 18 }}>Neuen Kunden erstellen</h2>

        <div style={gridStyle}>
          <input
            placeholder="Firmenname, z. B. KFZ Müller"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={inputStyle}
          />

          <input
            placeholder="Agent Key, z. B. kfz-mueller"
            value={agentKey}
            onChange={(e) => setAgentKey(e.target.value)}
            style={inputStyle}
          />

          <input
            placeholder="Benutzername, z. B. kfzadmin"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={inputStyle}
          />

          <input
            placeholder="Passwort"
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
        <h2 style={{ marginBottom: 16 }}>Kunden</h2>

        <div style={tenantGrid}>
          {tenants.map((tenant) => (
            <div
              key={tenant.id}
              onClick={() => openTenant(tenant)}
              style={tenantCard}
            >
              <h3 style={{ marginTop: 0, marginBottom: 8 }}>{tenant.name}</h3>

              <p style={{ color: "#94a3b8", marginBottom: 12 }}>
                Agent Key: {tenant.agent_key}
              </p>

              <p style={{ color: "#38bdf8", fontWeight: 700 }}>
                Dashboard öffnen →
              </p>
            </div>
          ))}
        </div>
      </section>
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

const headerStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: 30,
};

const formCard = {
  background: "rgba(15, 23, 42, 0.9)",
  padding: 24,
  borderRadius: 20,
  marginBottom: 34,
  border: "1px solid #1e293b",
  boxShadow: "0 20px 50px rgba(0,0,0,0.25)",
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 12,
  marginBottom: 16,
};

const tenantGrid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
  gap: 20,
};

const tenantCard = {
  background: "rgba(15, 23, 42, 0.92)",
  padding: 24,
  borderRadius: 20,
  cursor: "pointer",
  border: "1px solid #1e293b",
  transition: "transform 0.15s ease, border-color 0.15s ease",
};

const inputStyle = {
  width: "100%",
  padding: "12px 14px",
  borderRadius: 12,
  border: "1px solid #334155",
  background: "#020617",
  color: "white",
  outline: "none",
  fontSize: 14,
};

const primaryButton = {
  padding: "12px 18px",
  background: "linear-gradient(135deg, #2563eb, #0ea5e9)",
  color: "white",
  border: "none",
  borderRadius: 12,
  cursor: "pointer",
  fontWeight: 800,
};

const logoutButton = {
  padding: "10px 16px",
  background: "#ef4444",
  color: "white",
  border: "none",
  borderRadius: 10,
  cursor: "pointer",
  fontWeight: 700,
};