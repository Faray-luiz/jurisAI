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
  Shield,
} from "lucide-react";

type AdminSubTab = "logs" | "modelos" | "rag" | "custos" | "usuarios" | "missoes" | "governanca";

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
  { key: "governanca", label: "Governança & Tokens", icon: <Shield size={14} /> },
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
        <div style={{
          width: "32px",
          height: "32px",
          borderRadius: "50%",
          background: "#F6F5F3",
          border: "1.2px solid #E6DFD5",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
          boxShadow: "0 2px 6px rgba(0, 0, 0, 0.1)",
          flexShrink: 0,
          transition: "transform 0.3s ease, filter 0.3s ease"
        }} className="logo-icon">
          <svg viewBox="0 0 200 240" style={{ width: "90%", height: "90%" }}>
            {/* 1. Tail Feathers */}
            <path d="M 92,180 L 92,226 C 92,231 108,231 108,226 L 108,180 Z" fill="#3D332C" />
            <path d="M 92,216 L 92,226 C 92,231 108,231 108,226 L 108,216 Z" fill="#C5A676" />
            <path d="M 78,180 L 78,218 C 78,223 92,223 92,218 L 92,180 Z" fill="#3D332C" />
            <path d="M 78,208 L 78,218 C 78,223 92,223 92,218 L 92,208 Z" fill="#C5A676" />
            <path d="M 108,180 L 108,218 C 108,223 122,223 122,218 L 122,180 Z" fill="#3D332C" />
            <path d="M 108,208 L 108,218 C 108,223 122,223 122,218 L 122,208 Z" fill="#C5A676" />

            {/* 2. Main Body & Head */}
            <path d="M 75,20 C 50,20 38,32 38,62 C 38,82 28,102 28,132 C 28,180 58,198 100,198 C 142,198 172,180 172,132 C 172,102 162,82 162,62 C 162,32 150,20 125,20 Z" fill="#4A3B32" />

            {/* 3. Face Mask */}
            <path d="M 100,86 C 72,86 48,74 48,54 C 48,36 70,30 100,43 C 130,30 152,36 152,54 C 152,74 128,86 100,86 Z" fill="#CABEB2" />

            {/* 4. Eyes */}
            <circle cx="70" cy="56" r="21" fill="#FFFFFF" />
            <circle cx="70" cy="56" r="14" fill="#231B15" />
            <circle cx="75" cy="51" r="3.5" fill="#FFFFFF" />
            <circle cx="130" cy="56" r="21" fill="#FFFFFF" />
            <circle cx="130" cy="56" r="14" fill="#231B15" />
            <circle cx="135" cy="51" r="3.5" fill="#FFFFFF" />

            {/* 5. Eyebrows */}
            <path d="M 45,39 Q 100,46 155,39 L 155,34 Q 100,41 45,34 Z" fill="#231B15" />

            {/* 6. Beak */}
            <polygon points="93,56 107,56 100,73" fill="#C5A676" />

            {/* 7. White Belly */}
            <ellipse cx="100" cy="138" rx="50" ry="54" fill="#FFFFFF" />

            {/* 8. Belly Chevrons */}
            <path d="M 88,112 L 100,124 L 112,112" stroke="#CABEB2" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
            <path d="M 88,132 L 100,144 L 112,132" stroke="#CABEB2" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />

            {/* 9. Feather Tufts */}
            <path d="M 64,185 L 60,196 L 68,194 L 74,188 L 80,196 L 86,194 L 86,182 Z" fill="#4A3B32" />
            <path d="M 136,185 L 140,196 L 132,194 L 126,188 L 120,196 L 114,194 L 114,182 Z" fill="#4A3B32" />

            {/* 10. Legs */}
            <path d="M 68,188 L 68,206" stroke="#C5A676" stroke-width="7" stroke-linecap="round" fill="none" />
            <path d="M 76,188 L 76,208" stroke="#C5A676" stroke-width="7" stroke-linecap="round" fill="none" />
            <path d="M 84,188 L 84,206" stroke="#C5A676" stroke-width="7" stroke-linecap="round" fill="none" />
            <path d="M 116,188 L 116,206" stroke="#C5A676" stroke-width="7" stroke-linecap="round" fill="none" />
            <path d="M 124,188 L 124,208" stroke="#C5A676" stroke-width="7" stroke-linecap="round" fill="none" />
            <path d="M 132,188 L 132,206" stroke="#C5A676" stroke-width="7" stroke-linecap="round" fill="none" />

            {/* 11. Branch */}
            <path d="M 20,208 C 60,205 140,205 180,208" stroke="#997E68" stroke-width="12" stroke-linecap="round" fill="none" />
            <path d="M 150,205 C 165,195 175,185 180,175" stroke="#997E68" stroke-width="8" stroke-linecap="round" fill="none" />

            {/* 12. Claws */}
            <circle cx="68" cy="206" r="3.5" fill="#231B15" />
            <circle cx="76" cy="208" r="3.5" fill="#231B15" />
            <circle cx="84" cy="206" r="3.5" fill="#231B15" />
            <circle cx="116" cy="206" r="3.5" fill="#231B15" />
            <circle cx="124" cy="208" r="3.5" fill="#231B15" />
            <circle cx="132" cy="206" r="3.5" fill="#231B15" />
          </svg>
        </div>
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
