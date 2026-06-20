import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "GRiD Traffic Violation AI — Bangalore",
  description:
    "AI-powered traffic violation detection using YOLO, OCR, and RAG-based e-challan generation. Flipkart GRiD Theme 3.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  );
}
