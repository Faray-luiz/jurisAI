"use client";

import React, { useEffect } from "react";
import { X, Check, AlertTriangle, Clock, Copy } from "lucide-react";

interface CitationDrawerProps {
  isOpen: boolean;
  citation: any;
  onClose: () => void;
  onCopyText: (text: string) => void;
}

export default function CitationDrawer({ isOpen, citation, onClose, onCopyText }: CitationDrawerProps) {
  // Listen for escape key to close drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!citation) return null;

  const { status, citation: name, text, source, vigencia, conferido_em, correspondencia } = citation;

  return (
    <>
      {/* Scrim Overlay */}
      <div 
        className={`scrim ${isOpen ? "open" : ""}`} 
        onClick={onClose} 
        aria-hidden="true"
      />

      {/* Slide-out Drawer */}
      <div 
        className={`drawer ${isOpen ? "open" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label={`Detalhes da citação: ${name}`}
      >
        {/* Header */}
        <div className="drawer-header">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className={`badge ${status}`}>
              {status === "ok" ? "Verificado ✓" : status === "warn" ? "Não Verificado ⚠" : "Em Revisão ⏱"}
            </span>
            <button 
              onClick={onClose}
              style={{
                background: "transparent",
                border: "none",
                cursor: "pointer",
                color: "var(--ink-soft)",
                padding: "4px"
              }}
              aria-label="Fechar drawer"
            >
              <X size={18} />
            </button>
          </div>
          <h2 className="text-section" style={{ marginTop: "6px" }}>{name}</h2>
          <span style={{ fontSize: "11px", color: "var(--ink-faint)", textTransform: "uppercase", fontWeight: 600 }}>
            Fonte: {source}
          </span>
        </div>

        {/* Body */}
        <div className="drawer-body">
          {/* Main Text Content */}
          <div className="text-doc">
            <span className="text-label" style={{ fontSize: "11px", display: "block", marginBottom: "8px" }}>
              Conteúdo Factual / Dispositivo Oficial
            </span>
            
            {status === "ok" ? (
              <blockquote>
                {text}
              </blockquote>
            ) : status === "warn" ? (
              <blockquote className="warn-block">
                <div style={{ display: "flex", gap: "8px", color: "var(--ambar)", fontWeight: 600, fontSize: "13.5px", marginBottom: "6px" }}>
                  <AlertTriangle size={16} /> Dispositivo não verificado na fonte
                </div>
                {text}
              </blockquote>
            ) : (
              <blockquote className="review-block">
                <div style={{ display: "flex", gap: "8px", color: "var(--review-text)", fontWeight: 600, fontSize: "13.5px", marginBottom: "6px" }}>
                  <Clock size={16} /> Aguardando revisão humana
                </div>
                {text}
              </blockquote>
            )}
          </div>

          {/* Metadata Table */}
          <div style={{ marginTop: "10px" }}>
            <span className="text-label" style={{ fontSize: "11px", display: "block", marginBottom: "4px" }}>
              Parâmetros de Auditoria
            </span>
            <table className="meta-table">
              <tbody>
                <tr>
                  <td>Base Jurídica</td>
                  <td>{source || "N/A"}</td>
                </tr>
                <tr>
                  <td>Vigência</td>
                  <td style={{ color: vigencia === "Vigente" ? "var(--verde)" : "inherit" }}>
                    {vigencia}
                  </td>
                </tr>
                <tr>
                  <td>Verificado Em</td>
                  <td>{conferido_em}</td>
                </tr>
                <tr>
                  <td>Correspondência</td>
                  <td style={{ fontWeight: 600 }}>{correspondencia}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer */}
        <div className="drawer-footer">
          <button className="btn ghost" onClick={onClose}>
            Fechar
          </button>
          
          {status === "ok" && (
            <button 
              className="btn" 
              onClick={() => onCopyText(text)}
            >
              <Copy size={13} />
              <span>Inserir na Peça</span>
            </button>
          )}
          
          {status === "warn" && (
            <button 
              className="btn" 
              onClick={() => onCopyText(`[Revisão Pendente: ${name}]`)}
              style={{ background: "var(--ambar)" }}
            >
              <span>Enviar p/ Revisão</span>
            </button>
          )}
        </div>
      </div>
    </>
  );
}
