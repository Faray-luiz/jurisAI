"use client";

import React from "react";
import { Check, AlertTriangle, Clock } from "lucide-react";

interface CitationChipProps {
  rawText: string;
  citation: string;
  status: "ok" | "warn" | "review";
  onClick: () => void;
}

export default function CitationChip({ rawText, citation, status, onClick }: CitationChipProps) {
  const getIcon = () => {
    switch (status) {
      case "ok":
        return <Check size={12} strokeWidth={2.5} />;
      case "warn":
        return <AlertTriangle size={12} strokeWidth={2.5} />;
      case "review":
        return <Clock size={12} strokeWidth={2.5} />;
      default:
        return null;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <span
      className={`cite ${status}`}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`Citação ${citation}, status: ${status === "ok" ? "verificada" : status === "warn" ? "não verificada" : "em revisão"}`}
    >
      {getIcon()}
      <span>{citation}</span>
    </span>
  );
}
