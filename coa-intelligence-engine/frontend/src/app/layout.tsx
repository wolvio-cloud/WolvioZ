import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "CoA Intelligence Engine — Wolvio Intelligence",
  description:
    "AI-powered Certificate of Analysis extraction, validation, and audit trail for pharmaceutical QC",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
