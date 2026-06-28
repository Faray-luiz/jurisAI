"use client";

import React, { useState } from "react";
import {
  FileText,
  DollarSign,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
  ClipboardList,
  Cpu,
  BookOpen,
  Users,
  BarChart2,
  UserCog,
  Target,
  MessageSquare,
} from "lucide-react";

type AdminSubTab = "logs" | "modelos" | "rag" | "custos" | "usuarios" | "missoes";

interface SidebarProps {
  activeTab: "chat" | "missoes" | "auditoria";
  setActiveTab: (tab: "chat" | "missoes" | "auditoria") => void;
  adminSubTab: AdminSubTab;
  setAdminSubTab: (tab: AdminSubTab) => void;
  currentUser: any;
  usersList: any[];
  onUserChange: (email: string) => void;
  onLogout?: () => void;
  onSelectChatLivre?: () => void;
  onSelectMissoes?: () => void;
}

const GOV_ITEMS: { key: AdminSubTab; label: string; icon: React.ReactNode; sócioOnly?: boolean }[] = [
  { key: "logs",     label: "Auditoria & Muralha", icon: <ClipboardList size={14} /> },
  { key: "modelos",  label: "Modelos & Prompts",   icon: <Cpu size={14} /> },
  { key: "rag",      label: "Base RAG (Leis)",      icon: <BookOpen size={14} /> },
  { key: "custos",   label: "Custos & Orçamento",  icon: <BarChart2 size={14} /> },
  { key: "usuarios", label: "Usuários & Acesso",   icon: <UserCog size={14} />, sócioOnly: true },
  { key: "missoes",  label: "Missões",              icon: <Target size={14} />, sócioOnly: true },
];

export default function Sidebar({
  activeTab,
  setActiveTab,
  adminSubTab,
  setAdminSubTab,
  currentUser,
  usersList,
  onUserChange,
  onLogout,
  onSelectChatLivre,
  onSelectMissoes,
}: SidebarProps) {
  if (!currentUser) return null;

  const isGovAllowed =
    currentUser.role === "Sócio" || currentUser.role === "Compliance";

  // Auto-expand when on the audit tab
  const [govOpen, setGovOpen] = useState(activeTab === "auditoria");

  const quotaSpent = currentUser.quota_spent ?? 0;
  const quotaLimit = currentUser.quota_limit ?? 50.0;
  const quotaPercentage = Math.min(
    (quotaSpent / Math.max(quotaLimit, 1)) * 100,
    100
  );

  const handleGovItemClick = (key: AdminSubTab) => {
    setActiveTab("auditoria");
    setAdminSubTab(key);
  };

  const handleGovToggle = () => {
    if (!govOpen) {
      setActiveTab("auditoria");
    }
    setGovOpen((o) => !o);
  };

  return (
    <aside className="rail">
      {/* Brand Logo */}
      <div className="logo-container">
        <svg 
          className="logo-icon" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2.2" 
          strokeLinecap="round" 
          strokeLinejoin="round"
        >
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <circle cx="12" cy="11" r="1.5" fill="currentColor" />
          <line x1="12" y1="11" x2="9" y2="8" />
          <line x1="12" y1="11" x2="15" y2="8" />
          <line x1="12" y1="11" x2="12" y2="15" />
          <circle cx="9" cy="8" r="0.8" fill="currentColor" />
          <circle cx="15" cy="8" r="0.8" fill="currentColor" />
          <circle cx="12" cy="15" r="0.8" fill="currentColor" />
        </svg>
        <span className="logo-text">CSRM <span>AI</span></span>
      </div>

      {/* Nav Section */}
      <div className="nav-label">Navegação</div>

      {/* Chat Livre */}
      <button
        onClick={() => {
          setActiveTab("chat");
          if (onSelectChatLivre) onSelectChatLivre();
        }}
        className={`nav-item ${activeTab === "chat" ? "active" : ""}`}
      >
        <MessageSquare size={17} />
        <span>Chat Livre</span>
      </button>

      {/* Central de Missões */}
      <button
        onClick={() => {
          setActiveTab("missoes");
          if (onSelectMissoes) onSelectMissoes();
        }}
        className={`nav-item ${activeTab === "missoes" ? "active" : ""}`}
      >
        <Target size={17} />
        <span>Central de Missões</span>
      </button>

      {/* Governança — expandable, Sócio & Compliance only */}
      {isGovAllowed && (
        <div>
          {/* Parent toggle */}
          <button
            type="button"
            onClick={handleGovToggle}
            className={`nav-item ${activeTab === "auditoria" ? "active" : ""}`}
            style={{ width: "100%", justifyContent: "space-between" }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <ShieldCheck size={17} />
              <span>Governança</span>
            </span>
            <span style={{ opacity: 0.7, transition: "transform 0.2s", display: "flex" }}>
              {govOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </span>
          </button>

          {/* Submenu */}
          {govOpen && (
            <div
              style={{
                marginLeft: "16px",
                borderLeft: "2px solid rgba(255,255,255,0.08)",
                paddingLeft: "8px",
                display: "flex",
                flexDirection: "column",
                gap: "2px",
                marginTop: "2px",
                marginBottom: "4px",
              }}
            >
              {GOV_ITEMS.filter(
                (item) => !item.sócioOnly || currentUser.role === "Sócio"
              ).map((item) => {
                const isActive =
                  activeTab === "auditoria" && adminSubTab === item.key;
                return (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => handleGovItemClick(item.key)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      padding: "6px 10px",
                      borderRadius: "6px",
                      border: "none",
                      cursor: "pointer",
                      fontSize: "12px",
                      fontWeight: isActive ? 700 : 500,
                      fontFamily: "inherit",
                      textAlign: "left",
                      background: isActive
                        ? "rgba(255,255,255,0.12)"
                        : "transparent",
                      color: isActive
                        ? "var(--rail-bright)"
                        : "var(--rail-text)",
                      transition: "background 0.15s, color 0.15s",
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive)
                        (e.currentTarget as HTMLButtonElement).style.background =
                          "rgba(255,255,255,0.06)";
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive)
                        (e.currentTarget as HTMLButtonElement).style.background =
                          "transparent";
                    }}
                  >
                    <span style={{ opacity: 0.8 }}>{item.icon}</span>
                    {item.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Quota Card */}
      <div className="quota" style={{ marginTop: "auto" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: "11px",
            color: "var(--rail-bright)",
          }}
        >
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
        <span
          style={{
            fontSize: "10.5px",
            color:
              quotaPercentage >= 80
                ? "#e2cb97"
                : "var(--rail-text)",
            textAlign: "center",
          }}
        >
          {quotaPercentage >= 100
            ? "⚠️ Cota Excedida"
            : quotaPercentage >= 80
            ? "⚠️ Cota próxima ao limite (80%+)"
            : "Consumo sob controle"}
        </span>
      </div>

      {/* Session Switcher */}
      <div className="user-profile">
        <div className="avatar">
          {(currentUser.name || "")
            .split(" ")
            .map((n: string) => n[0])
            .join("")}
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            flex: 1,
            overflow: "hidden",
          }}
        >
          <span
            style={{
              fontSize: "12.5px",
              fontWeight: 600,
              color: "var(--rail-bright)",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {currentUser.name || "Sem Nome"}
          </span>
          <span style={{ fontSize: "10px", color: "var(--rail-text)" }}>
            {currentUser.role || "Advogado"}
          </span>
        </div>
      </div>

      <div
        style={{
          marginTop: "8px",
          display: "flex",
          flexDirection: "column",
          gap: "6px",
        }}
      >
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
            outline: "none",
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
              outline: "none",
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
              const el = document.getElementById(
                "custom-sso-email"
              ) as HTMLInputElement;
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
              cursor: "pointer",
            }}
          >
            Entrar
          </button>
        </div>
        <span
          style={{
            fontSize: "9.5px",
            color: "var(--rail-text)",
            textAlign: "center",
          }}
        >
          Digite e aperte Entrar para simular Google SSO
        </span>
        {onLogout && (
          <button
            onClick={onLogout}
            type="button"
            style={{
              marginTop: "16px",
              background: "transparent",
              color: "var(--rail-text)",
              border: "1px solid var(--rail-line)",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 500,
              padding: "6px",
              cursor: "pointer",
              textAlign: "center",
              width: "100%",
            }}
          >
            Sair da Conta
          </button>
        )}
      </div>
    </aside>
  );
}
