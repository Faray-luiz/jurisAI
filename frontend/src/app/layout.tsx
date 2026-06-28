import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CSRM AI — Inteligência Artificial Jurídica",
  description: "Camada unificada de IA do escritório com roteamento de modelos, barreira ética, e verificação síncrona de citações normativas.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
