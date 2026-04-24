async function getBookings() {
  const res = await fetch("http://localhost:3000/api/bookings", {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to load bookings");
  }

  return res.json();
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleString("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function getStatusColor(status: string) {
  switch (status) {
    case "confirmed":
      return "#22c55e"; // grün
    case "pending":
      return "#facc15"; // gelb
    case "email_sent":
      return "#60a5fa"; // blau
    default:
      return "#e2e8f0"; // grau
  }
}

export default async function Page() {
  const bookings = await getBookings();

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
          {bookings.length === 0 ? (
            <tr>
              <td colSpan={5} style={{ padding: "20px", textAlign: "center" }}>
                Keine Termine vorhanden
              </td>
            </tr>
          ) : (
            bookings.map((b: any) => (
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
                <td
                  style={{
                    ...td,
                    color: getStatusColor(b.status),
                    fontWeight: "bold",
                  }}
                >
                  {b.status}
                </td>
              </tr>
            ))
          )}
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