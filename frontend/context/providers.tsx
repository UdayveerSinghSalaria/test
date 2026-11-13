"use client";

import { AuthProvider } from "./auth-context";
import { AppProvider } from "./app-context";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AppProvider>
        {children}
      </AppProvider>
    </AuthProvider>
  );
}