"use client";

import { useEffect, useState } from "react";

type Booking = {
  id: string;
  name: string;
  email: string;
  requested_start: string;
  duration_minutes: number;
  status: string;
  calendar_event_id?: string | null;
};

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleString("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Berlin",
  });
}

function statusColor(status: string) {
  if (status === "confirmed") return "#22c55e";
  if (status === "pending") return "#facc15";
  if (status === "email_sent") return "#60a5fa";
  return "#e2e8f0";
}

export default function Page() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  async function loadBookings() {
    setLoading(true);
    const res = await fetch("/api/bookings", { cache: "no-store" });
    const data = await res.json();
    setBookings(data);
    setLoading(false);
  }

  async function deleteBooking(id: string) {
    if (!confirm("Termin wirklich löschen?")) return;
    await fetch(`/api/bookings/${id}`, { method: "DELETE" });
    await loadBookings();
  }

  async function confirmBooking(id: string) {
    await fetch(`/api/bookings/${id}`, { method: "POST" });
    await loadBookings();
  }

  useEffect(() => {
    loadBookings();
  }, []);

  const filtered =
    filter === "all" ? bookings : bookings.filter((b) => b.status === filter);

  return (
    <main
      style={{
        padding: 40,
        fontFamily: "Arial",
        background: "#0f172a",
        minHeight: "100vh",
        color: "#fff",
      }}
    >
      <h1 style={{ fontSize: 30, marginBottom: 20 }}>📅 Termine Übersicht</h1>

      <div style={{ marginBottom: 20, display: "flex", gap: 10 }}>
        {["all", "pending", "email_sent", "confirmed"].map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            style={{
              padding: "8px 14px",
              borderRadius: 8,
              border: "1px solid #334155",
              background: filter === s ? "#2563eb" : "#1e293b",
              color: "#fff",
              cursor: "pointer",
            }}
          >
            {s}
          </button>
        ))}

        <button
          onClick={loadBookings}
          style={{
            padding: "8px 14px",
            borderRadius: 8,
            border: "1px solid #334155",
            background: "#0f766e",
            color: "#fff",
            cursor: "pointer",
          }}
        >
          Aktualisieren
        </button>
      </div>

      {loading ? (
        <p>Lade Termine...</p>
      ) : (
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            background: "#1e293b",
            borderRadius: 8,
            overflow: "hidden",
          }}
        >
          <thead>
            <tr style={{ background: "#020617" }}>
              <th style={th}>Name</th>
              <th style={th}>E-Mail</th>
              <th style={th}>Datum</th>
              <th style={th}>Dauer</th>
              <th style={th}>Status</th>
              <th style={th}>Aktion</th>
            </tr>
          </thead>

          <tbody>
            {filtered.map((b) => (
              <tr key={b.id} style={{ borderBottom: "1px solid #334155" }}>
                <td style={td}>{b.name}</td>
                <td style={td}>{b.email}</td>
                <td style={td}>{formatDate(b.requested_start)}</td>
                <td style={td}>{b.duration_minutes} min</td>
                <td style={{ ...td, color: statusColor(b.status), fontWeight: 700 }}>
                  {b.status}
                </td>
                <td style={td}>
                  {b.status !== "confirmed" && (
                    <button onClick={() => confirmBooking(b.id)} style={confirmBtn}>
                      Bestätigen
                    </button>
                  )}
                  <button onClick={() => deleteBooking(b.id)} style={deleteBtn}>
                    Löschen
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}

const th = {
  padding: 12,
  textAlign: "left" as const,
};

const td = {
  padding: 12,
};

const confirmBtn = {
  marginRight: 8,
  padding: "6px 10px",
  borderRadius: 6,
  border: "none",
  background: "#16a34a",
  color: "#fff",
  cursor: "pointer",
};

const deleteBtn = {
  padding: "6px 10px",
  borderRadius: 6,
  border: "none",
  background: "#dc2626",
  color: "#fff",
  cursor: "pointer",
};