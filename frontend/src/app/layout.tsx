import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rabbitt AI — Sales Insight Automator",
  description:
    "Upload your sales CSV or XLSX file and receive an AI-generated executive summary delivered to your inbox instantly.",
  keywords: ["sales", "AI", "analytics", "executive summary", "Rabbitt AI"],
  openGraph: {
    title: "Rabbitt AI — Sales Insight Automator",
    description: "AI-powered sales data analysis and executive report generation.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
