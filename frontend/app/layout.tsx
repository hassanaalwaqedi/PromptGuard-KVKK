import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PromptGuard-KVKK",
  description: "Privacy Firewall for Generative AI",
  metadataBase: new URL("https://promptguard-kvkk.web.app"),
  openGraph: {
    type: "website",
    url: "https://promptguard-kvkk.web.app",
    siteName: "PromptGuard-KVKK",
    title: "PromptGuard-KVKK",
    description: "Privacy Firewall for Generative AI",
    images: [
      {
        url: "/promptguard-og.png",
        width: 1734,
        height: 907,
        alt: "PromptGuard-KVKK privacy firewall logo",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "PromptGuard-KVKK",
    description: "Privacy Firewall for Generative AI",
    images: ["/promptguard-og.png"],
  },
  icons: {
    icon: "/brand-mark.svg",
    shortcut: "/brand-mark.svg",
    apple: "/brand-mark.svg",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full bg-[#050914]">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
