"use client";

import React from "react";
import { Cpu, RefreshCw } from "lucide-react";

interface TopbarProps {
  activeTab: "chat" | "missoes" | "auditoria";
  selectedProcess: any;
  onClearChat?: () => void;
}

export default function Topbar({ activeTab, selectedProcess, onClearChat }: TopbarProps) {
  const isChatOrMissoes = activeTab === "chat" || activeTab === "missoes";

  return (
    <header className="topbar">
      {/* Breadcrumbs */}
      <div className="breadcrumb">
        <span style={{ color: "var(--ink-faint)" }}>CSRM AI</span>
        <span>/</span>
        <span style={{ fontWeight: 500, color: "var(--ink)" }}>
          {activeTab === "chat" 
            ? "Chat Livre" 
            : activeTab === "missoes" 
              ? "Central de Missões" 
              : "Muralha & Auditoria"}
        </span>
        {isChatOrMissoes && selectedProcess && (
          <>
            <span>/</span>
            <span style={{ color: "var(--bordo)", fontWeight: 600 }}>
              {selectedProcess.client} ({selectedProcess.process_number})
            </span>
          </>
        )}
      </div>

      {/* Model indicator & Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        {isChatOrMissoes && (
          <div className="pill-router">
            <div className="dot" />
            <Cpu size={12} style={{ color: "var(--bordo)" }} />
            <span style={{ fontSize: "11px", fontWeight: 600 }}>Roteador Invisível (Agnóstico)</span>
          </div>
        )}
        
        {isChatOrMissoes && onClearChat && (
          <button 
            className="btn ghost" 
            onClick={onClearChat}
            style={{ padding: "8px 12px", height: "34px", fontSize: "12px" }}
            title="Limpar Conversa"
          >
            <RefreshCw size={13} />
            <span>Limpar</span>
          </button>
        )}
      </div>
    </header>
  );
}
