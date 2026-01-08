'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { adminAPI, type AdminUser } from '@/lib/admin-api';

interface AdminAuthContextType {
  admin: AdminUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Check if user is authenticated on mount
    const checkAuth = async () => {
      const token = adminAPI.getToken();
      if (token) {
        try {
          const currentAdmin = await adminAPI.getCurrentAdmin();
          setAdmin(currentAdmin);
        } catch (error) {
          // Token is invalid, clear it
          adminAPI.setToken(null);
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    await adminAPI.login({ email, password });
    const currentAdmin = await adminAPI.getCurrentAdmin();
    setAdmin(currentAdmin);
    router.push('/admin/dashboard');
  };

  const logout = () => {
    adminAPI.logout();
    setAdmin(null);
    router.push('/admin/login');
  };

  return (
    <AdminAuthContext.Provider value={{ admin, isLoading, login, logout }}>
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
