'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: '📊' },
  { href: '/extracts', label: 'Extractos', icon: '📄' },
  { href: '/transactions', label: 'Transacciones', icon: '💳' },
  { href: '/budgets', label: 'Presupuestos', icon: '🎯' },
  { href: '/insights', label: 'Insights', icon: '💡' },
  { href: '/chat', label: 'Chat IA', icon: '🤖' },
  { href: '/settings', label: 'Configuracion', icon: '⚙️' },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:fixed md:inset-y-0 md:left-0 md:z-20 md:flex md:w-64 md:flex-col md:pt-14">
      <div className="flex flex-1 flex-col border-r border-gray-200 bg-white">
        <div className="flex h-14 items-center border-b border-gray-200 px-6">
          <span className="text-xl">💰</span>
          <span className="ml-2 text-lg font-bold text-primary-600">Finance Report</span>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                )}
              >
                <span className="text-lg">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center text-sm font-medium text-primary-600">
              U
            </div>
            <div className="flex-1 truncate">
              <p className="text-sm font-medium text-gray-900">Usuario</p>
              <p className="text-xs text-gray-500">usuario@email.com</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
