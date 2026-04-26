import { NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const ADMIN_SECRET = process.env.ADMIN_SECRET;

export async function GET() {
  const res = await fetch(`${API_URL}/admin/tenants`, {
    headers: {
      "x-admin-secret": ADMIN_SECRET ?? "",
    },
    cache: "no-store",
  });

  const data = await res.json();

  return NextResponse.json(data, {
    status: res.status,
  });
}

export async function POST(req: Request) {
  const body = await req.json();

  const res = await fetch(`${API_URL}/admin/tenants`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-admin-secret": ADMIN_SECRET ?? "",
    },
    body: JSON.stringify(body),
  });

  const data = await res.json();

  return NextResponse.json(data, {
    status: res.status,
  });
}