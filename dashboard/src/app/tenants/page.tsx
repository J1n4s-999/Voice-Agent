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

  useEffect(() => {
    const role = localStorage.getItem("role");

    if (role !== "super_admin") {
      router.push("/");
      return;
    }

    fetch("/api/tenants")
      .then((res) => res.json())
      .then((data) => {
        setTenants(data);
        setLoading(false);
      });
  }, [router]);

  function openTenant(tenant: Tenant) {
    localStorage.setItem("tenant_id", tenant.id);
    localStorage.setItem("tenant_name", tenant.name);

    router.push("/");
  }

  if (loading) {
    return (
      <div style={{ padding: 40, color: "white" }}>
        Lade Kunden...
      </div>
    );
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#020617",
        color: "white",
        padding: "40px",
      }}
    >
      <h1 style={{ fontSize: "32px", marginBottom: "30px" }}>
        Kundenübersicht
      </h1>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "20px",
        }}
      >
        {tenants.map((tenant) => (
          <div
            key={tenant.id}
            onClick={() => openTenant(tenant)}
            style={{
              background: "#0f172a",
              padding: "24px",
              borderRadius: "20px",
              cursor: "pointer",
              border: "1px solid #1e293b",
            }}
          >
            <h2>{tenant.name}</h2>

            <p style={{ color: "#94a3b8" }}>
              Agent Key: {tenant.agent_key}
            </p>

            <p style={{ color: "#38bdf8" }}>
              Dashboard öffnen →
            </p>
          </div>
        ))}
      </div>
    </main>
  );
}