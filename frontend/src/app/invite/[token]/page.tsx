"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Loader2, ShieldCheck, Eye, EyeOff } from "lucide-react";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function InvitePage() {
  const params = useParams();
  const router = useRouter();
  const token = params?.token as string;

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("A senha deve ter pelo menos 8 caracteres.");
      return;
    }
    if (password !== confirm) {
      setError("As senhas não coincidem.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/auth/set-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Erro ao ativar a conta.");
      } else {
        if (data.email) {
          localStorage.setItem("auth_email", data.email);
        }
        setSuccess(true);
        setTimeout(() => router.push("/"), 3000);
      }
    } catch {
      setError("Erro de conexão. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f5f4f0",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Segoe UI', Arial, sans-serif",
        padding: "24px",
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: "16px",
          boxShadow: "0 4px 32px rgba(0,0,0,0.10)",
          padding: "48px 44px",
          width: "100%",
          maxWidth: "440px",
        }}
      >
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "50%",
              background: "#7a2e2e",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: "12px",
            }}
          >
            <ShieldCheck size={26} color="#fff" />
          </div>
          <h1
            style={{
              fontSize: "22px",
              fontWeight: 800,
              color: "#1a1a1a",
              margin: "0 0 4px 0",
              letterSpacing: "-0.3px",
            }}
          >
            🛡️ CSRM AI
          </h1>
          <p style={{ fontSize: "13px", color: "#888", margin: 0 }}>
            Ativação de Conta
          </p>
        </div>

        {success ? (
          <div
            style={{
              textAlign: "center",
              padding: "24px",
              background: "rgba(0,160,80,0.06)",
              borderRadius: "12px",
              border: "1px solid rgba(0,160,80,0.2)",
            }}
          >
            <div style={{ fontSize: "40px", marginBottom: "12px" }}>✅</div>
            <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#1a1a1a", margin: "0 0 8px 0" }}>
              Conta ativada com sucesso!
            </h2>
            <p style={{ fontSize: "13px", color: "#666", margin: 0 }}>
              Redirecionando para o CSRM AI...
            </p>
          </div>
        ) : (
          <>
            <h2
              style={{
                fontSize: "18px",
                fontWeight: 700,
                color: "#1a1a1a",
                marginBottom: "6px",
              }}
            >
              Defina sua senha de acesso
            </h2>
            <p
              style={{
                fontSize: "13px",
                color: "#777",
                marginBottom: "28px",
                lineHeight: "1.5",
              }}
            >
              Escolha uma senha segura para acessar a plataforma. Use pelo menos 8 caracteres.
            </p>

            {error && (
              <div
                style={{
                  background: "rgba(180,0,0,0.06)",
                  border: "1px solid rgba(180,0,0,0.2)",
                  borderRadius: "8px",
                  padding: "12px 14px",
                  fontSize: "13px",
                  color: "#9a1a1a",
                  marginBottom: "20px",
                }}
              >
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "11px",
                    fontWeight: 700,
                    color: "#555",
                    marginBottom: "6px",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                  }}
                >
                  Nova Senha
                </label>
                <div style={{ position: "relative" }}>
                  <input
                    type={showPw ? "text" : "password"}
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Mínimo 8 caracteres"
                    style={{
                      width: "100%",
                      padding: "11px 44px 11px 14px",
                      borderRadius: "8px",
                      border: "1px solid #d8d4cc",
                      fontSize: "14px",
                      outline: "none",
                      boxSizing: "border-box",
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw((v) => !v)}
                    style={{
                      position: "absolute",
                      right: "12px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      color: "#aaa",
                      display: "flex",
                    }}
                  >
                    {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "11px",
                    fontWeight: 700,
                    color: "#555",
                    marginBottom: "6px",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                  }}
                >
                  Confirmar Senha
                </label>
                <input
                  type={showPw ? "text" : "password"}
                  required
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="Repita a senha"
                  style={{
                    width: "100%",
                    padding: "11px 14px",
                    borderRadius: "8px",
                    border: "1px solid #d8d4cc",
                    fontSize: "14px",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  background: "#7a2e2e",
                  color: "#fff",
                  border: "none",
                  borderRadius: "8px",
                  padding: "13px",
                  fontSize: "14px",
                  fontWeight: 700,
                  cursor: loading ? "not-allowed" : "pointer",
                  opacity: loading ? 0.7 : 1,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  marginTop: "4px",
                  fontFamily: "inherit",
                }}
              >
                {loading ? (
                  <>
                    <Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} />
                    Ativando...
                  </>
                ) : (
                  "Ativar minha conta →"
                )}
              </button>
            </form>

            <p
              style={{
                textAlign: "center",
                fontSize: "11px",
                color: "#bbb",
                marginTop: "24px",
              }}
            >
              Este link expira em 72 horas após o envio do convite.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
