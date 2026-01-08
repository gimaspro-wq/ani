import { AdminAuthProvider } from '@/contexts/admin-auth-context';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Admin Panel - Anirohi',
  description: 'Admin panel for managing anime content',
};

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminAuthProvider>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {children}
      </div>
    </AdminAuthProvider>
  );
}
