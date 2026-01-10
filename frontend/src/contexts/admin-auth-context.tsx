'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { adminAPI } from '@/lib/admin-api';
import type { AdminUser } from '@/types/admin';

function isAdminUser(value: unknown): value is AdminUser {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'email' in value
  );
}

interface AdminAuthContextType {
  admin: AdminUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  authError: string | null;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Check if user is authenticated on mount
    const checkAuth = async () => {
      const token = adminAPI.getToken();
      if (token) {
        try {
          const currentAdmin: unknown = await adminAPI.getCurrentAdmin();
          if (isAdminUser(currentAdmin)) {
            setAdmin(currentAdmin);
            setAuthError(null);
          } else {
            setAdmin(null);
          }
        } catch (error: unknown) {
          // Token is invalid, clear it
          adminAPI.setToken(null);
          if (typeof error === 'object' && error !== null && 'status' in error && (error as { status?: number }).status === 403) {
            setAuthError('Access denied');
          }
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    await adminAPI.login({ email, password });
    const currentAdmin: unknown = await adminAPI.getCurrentAdmin();
    if (isAdminUser(currentAdmin)) {
      setAdmin(currentAdmin);
      setAuthError(null);
      router.push('/admin/dashboard');
    } else {
      setAdmin(null);
    }
  };

  const logout = () => {
    adminAPI.logout();
    setAdmin(null);
    router.push('/admin/login');
  };

  return (
    <AdminAuthContext.Provider value={{ admin, isLoading, login, logout, authError }}>
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth() {
  const context = useContext(AdminAuthContext);
  if (context === undefined) {
    throw new Error('useAdminAuth must be used within an AdminAuthProvider');
  }
  return context;
}
