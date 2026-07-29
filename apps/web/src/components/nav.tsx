import Link from "next/link";

const NAV_LINKS = [{ href: "/dashboard", label: "Dashboard" }];

export function Nav() {
  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex h-14 max-w-5xl items-center gap-6 px-4">
        <Link href="/dashboard" className="font-semibold tracking-tight">
          OpsPilot
        </Link>
        <nav className="flex items-center gap-4 text-sm text-muted-foreground">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
