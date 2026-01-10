'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAdminAuth } from '@/contexts/admin-auth-context';

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { admin, isLoading, authError } = useAdminAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !admin && !authError) {
      router.push('/admin/login');
    }
  }, [admin, authError, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (authError) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="max-w-md w-full rounded-md bg-red-50 dark:bg-red-900/20 p-6 text-center">
          <h2 className="text-lg font-semibold text-red-800 dark:text-red-100">Access denied</h2>
          <p className="mt-2 text-sm text-red-700 dark:text-red-200">You do not have permission to access this area.</p>
          <button
            onClick={() => router.push('/admin/login')}
            className="mt-4 inline-flex items-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-500"
          >
            Return to login
          </button>
        </div>
      </div>
    );
  }

  if (!admin) {
    return null;
  }

  return <>{children}</>;
}
