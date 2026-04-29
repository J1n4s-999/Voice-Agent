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
  google_meet_link?: string | null;
};

type FormState = {
  name: string;
  email: string;
  requested_start: string;
  duration_minutes: string;
};

const emptyForm: FormState = {
  name: "",
  email: "",
  requested_start: "",
  duration_minutes: "30",
};

export default function BookingsPage() {
  const router = useRouter();

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [actionMessage, setActionMessage] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Booking | null>(null);

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
    setBookings(Array.isArray(data) ? data : []);
    setLoading(false);
  }

  useEffect(() => {
    loadBookings();
  }, []);

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleString("de-DE", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Europe/Berlin",
    });
  }

  function toDatetimeLocal(dateString: string) {
    const date = new Date(dateString);
    const offset = date.getTimezoneOffset();
    const local = new Date(date.getTime() - offset * 60 * 1000);
    return local.toISOString().slice(0, 16);
  }

  function toBackendDate(value: string) {
    return new Date(value).toISOString();
  }

  function resetForm() {
    setForm(emptyForm);
    setEditingId(null);
  }

  function startEdit(booking: Booking) {
    setEditingId(booking.id);
    setForm({
      name: booking.name,
      email: booking.email,
      requested_start: toDatetimeLocal(booking.requested_start),
      duration_minutes: String(booking.duration_minutes),
    });

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function saveBooking(e: React.FormEvent) {
    e.preventDefault();

    const tenantId = localStorage.getItem("tenant_id");

    if (!tenantId) {
      router.push("/login");
      return;
    }

    if (!form.name || !form.email || !form.requested_start || !form.duration_minutes) {
      alert("Bitte alle Felder ausfüllen.");
      return;
    }

    setSaving(true);
    setActionMessage(editingId ? "Termin wird aktualisiert..." : "Termin wird erstellt...");

    const payload = {
      tenant_id: tenantId,
      name: form.name,
      email: form.email,
      requested_start: toBackendDate(form.requested_start),
      duration_minutes: Number(form.duration_minutes),
    };

    const url = editingId
      ? `/api/bookings/${editingId}?tenant_id=${tenantId}`
      : "/api/bookings";

    const method = editingId ? "PATCH" : "POST";

    const body = editingId
      ? {
          name: payload.name,
          email: payload.email,
          requested_start: payload.requested_start,
          duration_minutes: payload.duration_minutes,
        }
      : payload;

    const res = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => null);
      setSaving(false);
      setActionMessage("");
      alert(data?.detail || "Fehler beim Speichern.");
      return;
    }

    resetForm();
    await loadBookings();

    setSaving(false);
    setActionMessage("");
  }

  async function performDelete() {
    if (!deleteTarget) return;

    const tenantId = localStorage.getItem("tenant_id");

    if (!tenantId) {
      router.push("/login");
      return;
    }

    setDeleteTarget(null);
    setActionMessage("Termin wird gelöscht...");

    const res = await fetch(`/api/bookings/${deleteTarget.id}?tenant_id=${tenantId}`, {
      method: "DELETE",
    });

    if (!res.ok) {
      setActionMessage("");
      alert("Fehler beim Löschen.");
      return;
    }

    await loadBookings();
    setActionMessage("");
  }

  async function confirmBooking(id: string) {
    const tenantId = localStorage.getItem("tenant_id");

    if (!tenantId) {
      router.push("/login");
      return;
    }

    setActionMessage("Termin wird bestätigt und im Google Kalender eingetragen...");

    const res = await fetch(`/api/bookings/${id}/confirm?tenant_id=${tenantId}`, {
      method: "POST",
    });

    if (!res.ok) {
      setActionMessage("");
      alert("Fehler beim Bestätigen.");
      return;
    }

    await loadBookings();
    setActionMessage("");
  }

  const buttonsDisabled = Boolean(actionMessage) || saving;

  if (loading) {
    return (
      <main style={pageStyle}>
        <p>Lade Termine...</p>
      </main>
    );
  }

  return (
    <main style={pageStyle}>
      {actionMessage && (
        <div style={overlayStyle}>
          <div style={loadingModalStyle}>
            <div style={spinnerStyle} />
            <h2 style={{ marginBottom: 8 }}>Bitte warten</h2>
            <p style={{ color: "#94a3b8", margin: 0 }}>{actionMessage}</p>
          </div>
        </div>
      )}

      {deleteTarget && (
        <div style={overlayStyle}>
          <div style={confirmModalStyle}>
            <h2 style={{ marginTop: 0 }}>Termin löschen?</h2>
            <p style={{ color: "#cbd5e1", lineHeight: 1.6 }}>
              Möchtest du den Termin von{" "}
              <strong>{deleteTarget.name}</strong> am{" "}
              <strong>{formatDate(deleteTarget.requested_start)}</strong>{" "}
              wirklich löschen?
            </p>
            <p style={{ color: "#94a3b8", fontSize: 14 }}>
              Falls der Termin bereits im Google Kalender eingetragen ist, wird
              er dort ebenfalls gelöscht.
            </p>

            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
              <button
                onClick={() => setDeleteTarget(null)}
                style={secondaryButton}
              >
                Abbrechen
              </button>

              <button
                onClick={performDelete}
                style={deleteButton}
              >
                Ja, löschen
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={headerStyle}>
        <button onClick={() => router.push("/")} style={backButton}>
          ← Zurück
        </button>

        <div>
          <h1 style={{ margin: 0, fontSize: 32 }}>Terminübersicht</h1>
          <p style={{ color: "#94a3b8", marginTop: 8 }}>
            Termine anzeigen, erstellen, bearbeiten, bestätigen oder löschen.
          </p>
        </div>
      </div>

      <section style={formCard}>
        <h2 style={{ marginTop: 0 }}>
          {editingId ? "Termin bearbeiten" : "Neuen Termin erstellen"}
        </h2>

        <form onSubmit={saveBooking} style={formGrid}>
          <input
            placeholder="Name"
            value={form.name}
            disabled={buttonsDisabled}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            style={inputStyle}
          />

          <input
            placeholder="E-Mail"
            type="email"
            value={form.email}
            disabled={buttonsDisabled}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            style={inputStyle}
          />

          <input
            type="datetime-local"
            value={form.requested_start}
            disabled={buttonsDisabled}
            onChange={(e) =>
              setForm({ ...form, requested_start: e.target.value })
            }
            style={inputStyle}
          />

          <input
            placeholder="Dauer in Minuten"
            type="number"
            value={form.duration_minutes}
            disabled={buttonsDisabled}
            onChange={(e) =>
              setForm({ ...form, duration_minutes: e.target.value })
            }
            style={inputStyle}
          />

          <div style={{ display: "flex", gap: 10 }}>
            <button type="submit" disabled={buttonsDisabled} style={primaryButton}>
              {saving
                ? "Speichern..."
                : editingId
                ? "Änderungen speichern"
                : "Termin erstellen"}
            </button>

            {editingId && (
              <button
                type="button"
                onClick={resetForm}
                disabled={buttonsDisabled}
                style={secondaryButton}
              >
                Abbrechen
              </button>
            )}
          </div>
        </form>

        <p style={{ color: "#94a3b8", marginBottom: 0 }}>
          Hinweis: Manuell erstellte Termine werden direkt als bestätigt gespeichert
          und automatisch im verbundenen Google Kalender erstellt.
        </p>
      </section>

      <div style={tableWrapper}>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Name</th>
              <th style={thStyle}>E-Mail</th>
              <th style={thStyle}>Datum</th>
              <th style={thStyle}>Dauer</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Meet</th>
              <th style={thStyle}>Aktionen</th>
            </tr>
          </thead>

          <tbody>
            {bookings.length === 0 ? (
              <tr>
                <td style={tdStyle} colSpan={7}>
                  Keine Termine vorhanden.
                </td>
              </tr>
            ) : (
              bookings.map((booking) => (
                <tr key={booking.id}>
                  <td style={tdStyle}>{booking.name}</td>
                  <td style={tdStyle}>{booking.email}</td>
                  <td style={tdStyle}>{formatDate(booking.requested_start)}</td>
                  <td style={tdStyle}>{booking.duration_minutes} min</td>
                  <td style={tdStyle}>{booking.status}</td>
                  <td style={tdStyle}>
                    {booking.google_meet_link ? (
                      <a
                        href={booking.google_meet_link}
                        target="_blank"
                        rel="noreferrer"
                        style={{ color: "#38bdf8" }}
                      >
                        Öffnen
                      </a>
                    ) : (
                      "-"
                    )}
                  </td>

                  <td style={tdStyle}>
                    <button
                      disabled={buttonsDisabled}
                      onClick={() => startEdit(booking)}
                      style={editButton}
                    >
                      Bearbeiten
                    </button>

                    {booking.status !== "confirmed" && (
                      <button
                        disabled={buttonsDisabled}
                        onClick={() => confirmBooking(booking.id)}
                        style={confirmButton}
                      >
                        Bestätigen
                      </button>
                    )}

                    <button
                      disabled={buttonsDisabled}
                      onClick={() => setDeleteTarget(booking)}
                      style={deleteButton}
                    >
                      Löschen
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <style jsx>{`
        @keyframes spin {
            from {
            transform: rotate(0deg);
            }
            to {
            transform: rotate(360deg);
            }
        }
        `}</style>
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
  alignItems: "center",
  gap: "20px",
  marginBottom: "30px",
};

const formCard = {
  background: "rgba(15, 23, 42, 0.92)",
  border: "1px solid #1e293b",
  borderRadius: 22,
  padding: 24,
  marginBottom: 28,
  boxShadow: "0 20px 50px rgba(0,0,0,0.25)",
};

const formGrid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 12,
  alignItems: "center",
  marginBottom: 14,
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

const tableWrapper = {
  background: "#0f172a",
  borderRadius: "16px",
  padding: "20px",
  overflowX: "auto" as const,
  border: "1px solid #1e293b",
};

const tableStyle = {
  width: "100%",
  borderCollapse: "collapse" as const,
};

const thStyle = {
  textAlign: "left" as const,
  padding: "14px",
  borderBottom: "1px solid #334155",
  color: "#cbd5e1",
};

const tdStyle = {
  padding: "14px",
  borderBottom: "1px solid #1e293b",
  color: "#e2e8f0",
};

const primaryButton = {
  background: "linear-gradient(135deg, #2563eb, #0ea5e9)",
  color: "white",
  border: "none",
  padding: "10px 14px",
  borderRadius: 10,
  cursor: "pointer",
  fontWeight: 800,
};

const secondaryButton = {
  background: "#334155",
  color: "white",
  border: "none",
  padding: "10px 14px",
  borderRadius: 10,
  cursor: "pointer",
  fontWeight: 700,
};

const editButton = {
  background: "#475569",
  color: "white",
  border: "none",
  padding: "8px 12px",
  borderRadius: "8px",
  cursor: "pointer",
  marginRight: "8px",
};

const confirmButton = {
  background: "#2563eb",
  color: "white",
  border: "none",
  padding: "8px 12px",
  borderRadius: "8px",
  cursor: "pointer",
  marginRight: "8px",
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

const overlayStyle = {
  position: "fixed" as const,
  inset: 0,
  background: "rgba(2, 6, 23, 0.76)",
  backdropFilter: "blur(6px)",
  zIndex: 1000,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 24,
};

const loadingModalStyle = {
  width: "100%",
  maxWidth: 420,
  background: "#0f172a",
  border: "1px solid #334155",
  borderRadius: 22,
  padding: 30,
  textAlign: "center" as const,
  boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
};

const confirmModalStyle = {
  width: "100%",
  maxWidth: 480,
  background: "#0f172a",
  border: "1px solid #334155",
  borderRadius: 22,
  padding: 28,
  boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
};

const spinnerStyle = {
  width: 42,
  height: 42,
  borderRadius: "50%",
  border: "4px solid #334155",
  borderTopColor: "#38bdf8",
  margin: "0 auto 18px",
  animation: "spin 1s linear infinite",
};