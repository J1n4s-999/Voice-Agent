import { NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const ADMIN_SECRET = process.env.ADMIN_SECRET;

export async function GET() {
  const res = await fetch(`${API_URL}/admin/bookings?tenant_id=default`, {
    headers: { "x-admin-secret": ADMIN_SECRET ?? "" },
    cache: "no-store",
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}