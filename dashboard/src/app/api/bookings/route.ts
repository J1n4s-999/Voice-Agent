import { NextResponse } from "next/server";

export async function GET() {
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/bookings`,
    {
      headers: {
        "x-admin-secret": process.env.ADMIN_SECRET!,
      },
      cache: "no-store",
    }
  );

  const data = await res.json();

  return NextResponse.json(data);
}