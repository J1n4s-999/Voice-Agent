"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardHome() {
  const router = useRouter();

  useEffect(() => {
    const username = localStorage.getItem("username");

    if (!username) {
      router.push("/login");
    }
  }, [router]);

  function logout() {
    localStorage.removeItem("username");
    localStorage.removeItem("tenant_id");
    localStorage.removeItem("role");

    router.push("/login");
  }

  const cardStyle = {
    background: "#0f172a",
    border: "1px solid #1e293b",
    borderRadius: "18px",
    padding: "28px",
    width: "100%",
    maxWidth: "500px",
    cursor: "pointer",
    transition: "0.2s",
  };

  return (
    <main
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at top left, #1d4ed8 0, transparent 25%), #020617",
        color: "white",
        padding: "40px",
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "600px",
        }}
      >
        <div
          style={{
            marginBottom: "40px",
            textAlign: "center",
          }}
        >
          <h1
            style={{
              fontSize: "36px",
              marginBottom: "10px",
            }}
          >
            Dashboard
          </h1>

          <p
            style={{
              color: "#94a3b8",
              fontSize: "16px",
            }}
          >
            Verwalte deinen Voice Agent
          </p>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "20px",
            alignItems: "center",
          }}
        >
          <div
            style={cardStyle}
            onClick={() => router.push("/bookings")}
          >
            <h2>📅 Terminübersicht</h2>
            <p>Alle Buchungen verwalten</p>
          </div>

          <div
            style={cardStyle}
            onClick={() => router.push("/settings")}
          >
            <h2>⚙️ Einstellungen</h2>
            <p>Google Kalender verbinden</p>
          </div>

          <div
            style={cardStyle}
            onClick={() => router.push("/availability")}
          >
            <h2>🕒 Öffnungszeiten</h2>
            <p>Urlaub, Buffer & Zeiten verwalten</p>
          </div>

          <button
            onClick={logout}
            style={{
              marginTop: "20px",
              background: "#dc2626",
              border: "none",
              color: "white",
              padding: "14px 30px",
              borderRadius: "12px",
              cursor: "pointer",
              fontWeight: "bold",
              fontSize: "15px",
            }}
          >
            Logout
          </button>
        </div>
      </div>
    </main>
  );
}