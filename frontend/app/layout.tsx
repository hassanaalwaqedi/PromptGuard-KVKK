import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PromptGuard-KVKK",
  description: "Privacy Firewall for Generative AI",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full bg-[#050914]">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
