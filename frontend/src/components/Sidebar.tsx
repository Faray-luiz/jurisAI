"use client";

import React from "react";
import { Folder, FileText, Settings, DollarSign, User, ShieldCheck } from "lucide-react";

interface SidebarProps {
  activeTab: "chat" | "auditoria";
  setActiveTab: (tab: "chat" | "auditoria") => void;
  currentUser: any;
  usersList: any[];
  onUserChange: (email: string) => void;
}

export default function Sidebar({
  activeTab,
  setActiveTab,
  currentUser,
  usersList,
  onUserChange
}: SidebarProps) {
  if (!currentUser) return null;

  const quotaSpent = currentUser.quota_spent ?? 0;
  const quotaLimit = currentUser.quota_limit ?? 50.0;
  const quotaPercentage = Math.min(
    (quotaSpent / Math.max(quotaLimit, 1)) * 100,
    100
  );

  return (
    <aside className="rail">
      {/* Brand Logo */}
      <div className="logo-container">
        <div className="logo-seal">J</div>
        <span className="logo-text">JurisAI</span>
      </div>

      {/* Nav Section */}
      <div className="nav-label">Navegação</div>
      
      <button
        onClick={() => setActiveTab("chat")}
        className={`nav-item ${activeTab === "chat" ? "active" : ""}`}
      >
        <FileText size={17} />
        <span>Chat & Missões</span>
      </button>

      {/* Segregation of duties: only Sócio and Compliance can audit logs */}
      {(currentUser.role === "Sócio" || currentUser.role === "Compliance") && (
        <button
          onClick={() => setActiveTab("auditoria")}
          className={`nav-item ${activeTab === "auditoria" ? "active" : ""}`}
        >
          <ShieldCheck size={17} />
          <span>Muralha & Auditoria</span>
        </button>
      )}

      {/* Quota Card */}
      <div className="quota" style={{ marginTop: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--rail-bright)" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <DollarSign size={12} /> Cota Mensal
          </span>
          <span>
            ${quotaSpent.toFixed(2)} / ${quotaLimit.toFixed(2)}
          </span>
        </div>
        <div className="bar">
          <i style={{ width: `${quotaPercentage}%` }}></i>
        </div>
        <span style={{ fontSize: "10.5px", color: quotaPercentage >= 80 ? "#e2cb97" : "var(--rail-text)", textAlign: "center" }}>
          {quotaPercentage >= 100 
            ? "⚠️ Cota Excedida" 
            : quotaPercentage >= 80 
            ? "⚠️ Cota próxima ao limite (80%+)" 
            : "Consumo sob controle"}
        </span>
      </div>

      {/* Session Switcher (Simulated SSO) */}
      <div className="user-profile">
        <div className="avatar">
          {(currentUser.name || "").split(" ").map((n: string) => n[0]).join("")}
        </div>
        <div style={{ display: "flex", flexDirection: "column", flex: 1, overflow: "hidden" }}>
          <span style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--rail-bright)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {currentUser.name || "Sem Nome"}
          </span>
          <span style={{ fontSize: "10px", color: "var(--rail-text)" }}>
            {currentUser.role || "Advogado"}
          </span>
        </div>
      </div>

      <div style={{ marginTop: "8px", display: "flex", flexDirection: "column", gap: "6px" }}>
        <select
          value={currentUser.email}
          onChange={(e) => onUserChange(e.target.value)}
          style={{
            width: "100%",
            background: "var(--rail-2)",
            color: "var(--rail-bright)",
            border: "1px solid var(--rail-line)",
            borderRadius: "6px",
            fontSize: "11.5px",
            padding: "6px",
            fontFamily: "inherit",
            cursor: "pointer",
            outline: "none"
          }}
        >
          {usersList.map((u) => (
            <option key={u.email} value={u.email}>
              Simular: {u.name} ({u.role})
            </option>
          ))}
        </select>

        {/* Custom email input for Google SSO Auto-Onboarding */}
        <div style={{ display: "flex", gap: "4px" }}>
          <input
            type="email"
            id="custom-sso-email"
            placeholder="novo.adv@jurisai.com.br"
            style={{
              flex: 1,
              background: "var(--rail-2)",
              color: "var(--rail-bright)",
              border: "1px solid var(--rail-line)",
              borderRadius: "6px",
              fontSize: "11px",
              padding: "5px 8px",
              fontFamily: "inherit",
              outline: "none"
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                const val = (e.target as HTMLInputElement).value.trim();
                if (val && val.includes("@")) {
                  onUserChange(val);
                  (e.target as HTMLInputElement).value = "";
                }
              }
            }}
          />
          <button
            type="button"
            onClick={() => {
              const el = document.getElementById("custom-sso-email") as HTMLInputElement;
              if (el && el.value && el.value.includes("@")) {
                onUserChange(el.value.trim());
                el.value = "";
              }
            }}
            style={{
              background: "var(--bordo)",
              color: "#fff",
              border: "none",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 600,
              padding: "4px 8px",
              cursor: "pointer"
            }}
          >
            Entrar
          </button>
        </div>
        <span style={{ fontSize: "9.5px", color: "var(--rail-text)", textAlign: "center" }}>
          Digite e aperte Entrar para simular Google SSO
        </span>
      </div>
    </aside>
  );
}
