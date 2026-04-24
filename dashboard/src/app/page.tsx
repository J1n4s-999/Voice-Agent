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
  return new Date(dateString).toLocaleString("de-DE");
}

function getStatusColor(status: string) {
  switch (status) {
    case "confirmed":
      return "text-green-500";
    case "pending":
      return "text-yellow-500";
    case "email_sent":
      return "text-blue-500";
    default:
      return "text-gray-400";
  }
}

export default async function Home() {
  const bookings = await getBookings();

  return (
    <main className="p-10">
      <h1 className="text-3xl font-bold mb-6">📅 Bookings</h1>

      <table className="w-full border border-gray-700 rounded-lg overflow-hidden">
        <thead className="bg-gray-800">
          <tr>
            <th className="p-3 text-left">Name</th>
            <th className="p-3 text-left">Email</th>
            <th className="p-3 text-left">Datum</th>
            <th className="p-3 text-left">Dauer</th>
            <th className="p-3 text-left">Status</th>
          </tr>
        </thead>

        <tbody>
          {bookings.map((b: any) => (
            <tr key={b.id} className="border-t border-gray-700">
              <td className="p-3">{b.name}</td>
              <td className="p-3">{b.email}</td>
              <td className="p-3">{formatDate(b.requested_start)}</td>
              <td className="p-3">{b.duration_minutes} min</td>
              <td className={`p-3 font-semibold ${getStatusColor(b.status)}`}>
                {b.status}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}