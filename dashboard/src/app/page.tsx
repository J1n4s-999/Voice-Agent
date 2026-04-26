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

  useEffect(() => {
    loadBookings();
  }, []);

  async function deleteBooking(id: string) {
    const tenant_id = localStorage.getItem("tenant_id");

    const res = await fetch(
      `/api/bookings/${id}?tenant_id=${tenant_id}`,
      {
        method: "DELETE",
      }
    );

    if (res.ok) {
      loadBookings();
    }
  }

  async function confirmBooking(id: string) {
    const tenant_id = localStorage.getItem("tenant_id");

    const res = await fetch(
      `/api/bookings/${id}/confirm?tenant_id=${tenant_id}`,
      {
        method: "POST",
      }
    );

    if (res.ok) {
      loadBookings();
    }
  }

  function logout() {
    localStorage.removeItem("tenant_id");
    localStorage.removeItem("username");
    window.location.href = "/login";
  }

  return (
    <main
      style={{
        padding: "40px",
        background: "#0f172a",
        minHeight: "100vh",
        color: "white",
        fontFamily: "Arial",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: "20px",
        }}
      >
        <h1>📅 Termine Übersicht</h1>

        <button
          onClick={logout}
          style={{
            background: "#ef4444",
            color: "white",
            border: "none",
            padding: "10px 16px",
            borderRadius: "8px",
            cursor: "pointer",
          }}
        >
          Logout
        </button>
      </div>

      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          background: "#1e293b",
          borderRadius: "10px",
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
            <th style={th}>Aktionen</th>
          </tr>
        </thead>

        <tbody>
          {bookings.map((b) => (
            <tr key={b.id}>
              <td style={td}>{b.name}</td>
              <td style={td}>{b.email}</td>
              <td style={td}>{formatDate(b.requested_start)}</td>
              <td style={td}>{b.duration_minutes} min</td>
              <td style={td}>{b.status}</td>

              <td style={td}>
                {b.status !== "confirmed" && (
                  <button
                    onClick={() => confirmBooking(b.id)}
                    style={{
                      background: "#22c55e",
                      color: "white",
                      border: "none",
                      padding: "8px 12px",
                      marginRight: "10px",
                      borderRadius: "6px",
                      cursor: "pointer",
                    }}
                  >
                    Bestätigen
                  </button>
                )}

                <button
                  onClick={() => deleteBooking(b.id)}
                  style={{
                    background: "#ef4444",
                    color: "white",
                    border: "none",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    cursor: "pointer",
                  }}
                >
                  Löschen
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}

const th = {
  padding: "14px",
  textAlign: "left" as const,
};

const td = {
  padding: "14px",
  borderBottom: "1px solid #334155",
};