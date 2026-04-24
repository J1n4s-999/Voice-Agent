import { NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const ADMIN_SECRET = process.env.ADMIN_SECRET;

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  const res = await fetch(`${API_URL}/admin/bookings/${id}`, {
    method: "DELETE",
    headers: { "x-admin-secret": ADMIN_SECRET ?? "" },
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  const res = await fetch(`${API_URL}/admin/bookings/${id}/confirm`, {
    method: "POST",
    headers: { "x-admin-secret": ADMIN_SECRET ?? "" },
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}