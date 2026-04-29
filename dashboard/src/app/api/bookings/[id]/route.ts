import { NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const ADMIN_SECRET = process.env.ADMIN_SECRET;

export async function DELETE(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const url = new URL(req.url);
  const tenantId = url.searchParams.get("tenant_id");

  const res = await fetch(`${API_URL}/admin/bookings/${id}?tenant_id=${tenantId}`, {
    method: "DELETE",
    headers: {
      "x-admin-secret": ADMIN_SECRET ?? "",
    },
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const url = new URL(req.url);
  const tenantId = url.searchParams.get("tenant_id");
  const body = await req.json();

  const res = await fetch(`${API_URL}/admin/bookings/${id}?tenant_id=${tenantId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "x-admin-secret": ADMIN_SECRET ?? "",
    },
    body: JSON.stringify(body),
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}