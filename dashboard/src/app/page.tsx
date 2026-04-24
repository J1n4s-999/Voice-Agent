"use client";

import { useEffect, useState } from "react";

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleString("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function Page() {
  const [bookings, setBookings] = useState<any[]>([]);

  useEffect(() => {
    async function loadBookings() {
      const tenant_id = localStorage.getItem("tenant_id");

      if (!tenant_id) {
        window.location.href = "/login";
        return;
      }

      const res = await fetch("/api/bookings", {
        headers: {
          "x-tenant-id": tenant_id,
        },
      });

      const data = await res.json();
      setBookings(data);
    }

    loadBookings();
  }, []);

  return (
    <main
      style={{
        padding: "40px",
        fontFamily: "Arial",
        background: "#0f172a",
        minHeight: "100vh",
        color: "#fff",
      }}
    >
      <h1 style={{ fontSize: "28px", marginBottom: "20px" }}>
        📅 Termine Übersicht
      </h1>

      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          background: "#1e293b",
          borderRadius: "8px",
          overflow: "hidden",
        }}
      >
        <thead>
          <tr style={{ background: "#020617", color: "#fff" }}>
            <th style={th}>Name</th>
            <th style={th}>E-Mail</th>
            <th style={th}>Datum</th>
            <th style={th}>Dauer</th>
            <th style={th}>Status</th>
          </tr>
        </thead>

        <tbody>
          {bookings.map((b) => (
            <tr
              key={b.id}
              style={{
                borderBottom: "1px solid #334155",
                color: "#e2e8f0",
              }}
            >
              <td style={td}>{b.name}</td>
              <td style={td}>{b.email}</td>
              <td style={td}>{formatDate(b.requested_start)}</td>
              <td style={td}>{b.duration_minutes} min</td>
              <td style={td}>{b.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}

const th = {
  padding: "12px",
  textAlign: "left" as const,
};

const td = {
  padding: "12px",
};