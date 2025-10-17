"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/" },
  { name: "Weeks", href: "/weeks" },
  { name: "Analytics", href: "/analytics" },
  { name: "Exports", href: "/exports" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="border-b bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 justify-between">
          <div className="flex">
            <div className="flex flex-shrink-0 items-center">
              <Link href="/" className="text-xl font-bold text-gray-900">
                TEQUILA
              </Link>
              <span className="ml-2 text-sm text-gray-500">
                Latin A Curriculum
              </span>
            </div>
            <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "inline-flex items-center border-b-2 px-1 pt-1 text-sm font-medium",
                    pathname === item.href
                      ? "border-blue-500 text-gray-900"
                      : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                  )}
                >
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center">
            <span className="text-sm text-gray-500">v1.2.0</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
