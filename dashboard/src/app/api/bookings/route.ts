import { NextResponse } from "next/server";

export async function GET() {
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/admin/bookings`,
    {
      headers: {
        "x-admin-secret": process.env.ADMIN_SECRET ?? "",
      },
      cache: "no-store",
    }
  );

  if (!res.ok) {
    return NextResponse.json(
      { error: "Failed to fetch bookings", status: res.status },
      { status: res.status }
    );
  }

  const data = await res.json();
  return NextResponse.json(data);
}