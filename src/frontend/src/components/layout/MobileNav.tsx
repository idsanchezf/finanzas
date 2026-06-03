'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const MOBILE_ITEMS = [
  { href: '/', label: 'Inicio', icon: '🏠' },
  { href: '/extracts', label: 'Extractos', icon: '📄' },
  { href: '/transactions', label: 'Gastos', icon: '💳' },
  { href: '/chat', label: 'Chat', icon: '🤖' },
  { href: '/settings', label: 'Ajustes', icon: '⚙️' },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 border-t border-gray-200 bg-white md:hidden">
      <div className="mx-auto flex max-w-lg items-center justify-around">
        {MOBILE_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex flex-col items-center gap-0.5 px-3 py-2 text-xs font-medium transition-colors',
                isActive ? 'text-primary-600' : 'text-gray-400 hover:text-gray-600'
              )}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
