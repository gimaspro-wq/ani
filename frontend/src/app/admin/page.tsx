'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAdminAuth } from '@/contexts/admin-auth-context';

export default function AdminPage() {
  const { admin, authState } = useAdminAuth();
  const router = useRouter();

  useEffect(() => {
    if (authState === 'loading') return;
    if (admin) {
      router.push('/admin/dashboard');
    } else {
      router.push('/admin/login');
    }
  }, [admin, authState, router]);

  return null;
}
