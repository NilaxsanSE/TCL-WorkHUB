import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TCL WorkHub",
  description: "Work hours, approval, payment, and invoice management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

