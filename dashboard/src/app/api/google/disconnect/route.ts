import { NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const ADMIN_SECRET = process.env.ADMIN_SECRET;

export async function DELETE(req: Request) {
  const tenantId = req.headers.get("x-tenant-id");

  const res = await fetch(`${API_URL}/admin/google/disconnect?tenant_id=${tenantId}`, {
    method: "DELETE",
    headers: {
      "x-admin-secret": ADMIN_SECRET ?? "",
    },
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}