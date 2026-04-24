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
    timeZone: "Europe/Berlin",
  });
}

export default async function Home() {
  const bookings = await getBookings();

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold mb-6">
        Termine
      </h1>

      <div className="space-y-4">
        {bookings.map((b: any) => (
          <div
            key={b.id}
            className="p-4 border rounded-xl shadow-sm"
          >
            <div className="font-semibold">
              {b.name}
            </div>

            <div className="text-sm text-gray-600">
              {b.email}
            </div>

            <div className="mt-2">
              📅 {formatDate(b.requested_start)}
            </div>

            <div>
              ⏱ {b.duration_minutes} Minuten
            </div>

            <div className="mt-2">
              Status:{" "}
              <span className="font-medium">
                {b.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}