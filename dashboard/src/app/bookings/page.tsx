"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Booking = {
  id: string;
  name: string;
  email: string;
  requested_start: string;
  duration_minutes: number;
  status: string;
  google_meet_link?: string;
};

export default function BookingsPage() {
  const router = useRouter();

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadBookings() {
  const tenantId = localStorage.getItem("tenant_id");

  if (!tenantId) {
    router.push("/login");
    return;
  }

  const res = await fetch("/api/bookings", {
    headers: {
      "x-tenant-id": tenantId,
    },
    cache: "no-store",
  });

  const data = await res.json();

  setBookings(data);
  setLoading(false);
  }

  useEffect(() => {
    loadBookings();
  }, []);

  async function deleteBooking(id: string) {
    const tenantId = localStorage.getItem("tenant_id");

    if (!confirm("Termin wirklich löschen?")) return;

    const res = await fetch(
      `/api/bookings/${id}?tenant_id=${tenantId}`,
      {
        method: "DELETE",
      }
    );

    if (res.ok) {
      loadBookings();
    } else {
      alert("Fehler beim Löschen.");
    }
  }

  async function confirmBooking(id: string) {
    const tenantId = localStorage.getItem("tenant_id");

    const res = await fetch(
      `/api/bookings/${id}/confirm?tenant_id=${tenantId}`,
      {
        method: "POST",
      }
    );

    if (res.ok) {
      loadBookings();
    } else {
      alert("Fehler beim Bestätigen.");
    }
  }

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleString("de-DE", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  }

  if (loading) {
    return (
      <main style={pageStyle}>
        <p>Lade Termine...</p>
      </main>
    );
  }

  return (
    <main style={pageStyle}>
      <div style={headerStyle}>
        <button
          onClick={() => router.push("/")}
          style={backButton}
        >
          ← Zurück
        </button>

        <h1 style={{ margin: 0 }}>Terminübersicht</h1>
      </div>

      <div style={tableWrapper}>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Name</th>
              <th style={thStyle}>E-Mail</th>
              <th style={thStyle}>Datum</th>
              <th style={thStyle}>Dauer</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Aktionen</th>
            </tr>
          </thead>

          <tbody>
            {bookings.map((booking) => (
              <tr key={booking.id}>
                <td style={tdStyle}>{booking.name}</td>
                <td style={tdStyle}>{booking.email}</td>
                <td style={tdStyle}>
                  {formatDate(booking.requested_start)}
                </td>
                <td style={tdStyle}>
                  {booking.duration_minutes} min
                </td>
                <td style={tdStyle}>
                  {booking.status}
                </td>

                <td style={tdStyle}>
                  {booking.status !== "confirmed" && (
                    <button
                      onClick={() =>
                        confirmBooking(booking.id)
                      }
                      style={confirmButton}
                    >
                      Bestätigen
                    </button>
                  )}

                  <button
                    onClick={() =>
                      deleteBooking(booking.id)
                    }
                    style={deleteButton}
                  >
                    Löschen
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}

const pageStyle = {
  minHeight: "100vh",
  background: "#020617",
  color: "white",
  padding: "40px",
};

const headerStyle = {
  display: "flex",
  alignItems: "center",
  gap: "20px",
  marginBottom: "30px",
};

const tableWrapper = {
  background: "#0f172a",
  borderRadius: "16px",
  padding: "20px",
  overflowX: "auto" as const,
};

const tableStyle = {
  width: "100%",
  borderCollapse: "collapse" as const,
};

const thStyle = {
  textAlign: "left" as const,
  padding: "14px",
  borderBottom: "1px solid #334155",
};

const tdStyle = {
  padding: "14px",
  borderBottom: "1px solid #1e293b",
};

const confirmButton = {
  background: "#2563eb",
  color: "white",
  border: "none",
  padding: "8px 12px",
  borderRadius: "8px",
  cursor: "pointer",
  marginRight: "10px",
};

const deleteButton = {
  background: "#dc2626",
  color: "white",
  border: "none",
  padding: "8px 12px",
  borderRadius: "8px",
  cursor: "pointer",
};

const backButton = {
  background: "transparent",
  color: "#60a5fa",
  border: "none",
  cursor: "pointer",
  fontSize: "16px",
};