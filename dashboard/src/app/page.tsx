async function getBookings() {
  const res = await fetch(
    process.env.NEXT_PUBLIC_API_URL + "/api/bookings",
    {
      cache: "no-store",
      headers: {
        "x-admin-secret": process.env.ADMIN_SECRET || "",
      },
    }
  );

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

export default async function Page() {
  const bookings = await getBookings();

  return (
    <main style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1 style={{ fontSize: "28px", marginBottom: "20px" }}>
        📅 Termine Übersicht
      </h1>

      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          background: "#fff",
        }}
      >
        <thead>
          <tr style={{ background: "#111827", color: "#fff" }}>
            <th style={th}>Name</th>
            <th style={th}>E-Mail</th>
            <th style={th}>Datum</th>
            <th style={th}>Dauer</th>
            <th style={th}>Status</th>
          </tr>
        </thead>

        <tbody>
          {bookings.map((b: any) => (
            <tr key={b.id} style={{ borderBottom: "1px solid #ddd" }}>
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