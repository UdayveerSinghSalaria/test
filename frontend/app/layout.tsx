import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Temporary neutral metadata — the product name comes from central config
// on the client. No permanent branding is baked in yet.
export const metadata: Metadata = {
  title: "AI Work Assistant",
  description: "Agentic personal work assistant (MVP preview)",
};

/** Applies the stored theme before paint to avoid a light flash. */
const themeInit = `
try {
  var t = localStorage.getItem("awa-theme") || "dark";
  document.documentElement.classList.toggle("dark", t === "dark");
} catch (e) {}
`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body className="min-h-full flex flex-col bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}
