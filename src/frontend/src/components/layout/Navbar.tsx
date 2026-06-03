'use client';

import Link from 'next/link';

export function Navbar() {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-gray-200 bg-white px-4 shadow-sm md:hidden">
      <Link href="/" className="flex items-center gap-2">
        <span className="text-xl">💰</span>
        <span className="text-lg font-bold text-primary-600">Finance Report</span>
      </Link>
      <button className="rounded-lg p-2 text-gray-500 hover:bg-gray-100">
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      </button>
    </header>
  );
}
