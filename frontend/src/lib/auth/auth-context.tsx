"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { backendAPI } from "@/lib/api/backend";
import { useLoginMerge } from "@/hooks/use-login-merge";
import { toast } from "sonner";

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
  isSyncing: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { triggerMerge, isMerging } = useLoginMerge();

  // Fetch current user on mount if authenticated
  const refreshUser = useCallback(async () => {
    if (!backendAPI.isAuthenticated()) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const response = await backendAPI.getCurrentUser();
      setUser(response);
    } catch (error) {
      console.error("Failed to fetch user:", error);
      // Token might be invalid, clear it
      backendAPI.clearAccessToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      try {
        await backendAPI.login(email, password);
        await refreshUser();
        
        // Trigger merge after successful login (non-blocking)
        triggerMerge();
      } catch (error) {
        // Re-throw to let the caller handle the error
        throw error;
      }
    },
    [refreshUser, triggerMerge]
  );

  const register = useCallback(
    async (email: string, password: string) => {
      try {
        await backendAPI.register(email, password);
        await refreshUser();
        
        // Trigger merge after successful registration (non-blocking)
        triggerMerge();
      } catch (error) {
        // Re-throw to let the caller handle the error
        throw error;
      }
    },
    [refreshUser, triggerMerge]
  );

  const logout = useCallback(async () => {
    try {
      await backendAPI.logout();
    } catch (error) {
      console.error("Logout error:", error);
      // Continue with logout even if server request fails
    } finally {
      setUser(null);
      toast.success("Logged out successfully");
    }
  }, []);

  const value = {
    isAuthenticated: !!user,
    user,
    isLoading,
    isSyncing: isMerging,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
