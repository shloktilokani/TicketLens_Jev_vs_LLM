import {
  Activity,
  Columns2,
  CircleCheck,
  CircleX,
  GitCompare,
  LayoutDashboard,
  Menu,
  Moon,
  Plus,
  Search,
  Settings,
  Sun,
  Ticket,
} from "lucide-react"
import { useTheme } from "next-themes"
import { useEffect, useState } from "react"
import { Link, NavLink, Outlet, useMatches, useNavigate } from "react-router"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet"
import { cn } from "@/lib/utils"
import { useProviderStatus } from "@/services/queries"

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/tickets", label: "Tickets", icon: Ticket },
  { to: "/compare", label: "Compare", icon: Columns2 },
  { to: "/comparisons", label: "Comparisons", icon: GitCompare },
  { to: "/executions", label: "AI Executions", icon: Activity },
  { to: "/settings", label: "Settings", icon: Settings },
]

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav aria-label="Main" className="flex flex-col gap-1">
      {NAV.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-muted",
              isActive && "bg-muted font-medium",
            )
          }
        >
          <Icon className="size-4" aria-hidden />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const dark = resolvedTheme === "dark"
  return (
    <Button
      variant="ghost"
      size="sm"
      className="justify-start"
      onClick={() => setTheme(dark ? "light" : "dark")}
    >
      {dark ? <Sun aria-hidden /> : <Moon aria-hidden />}
      {dark ? "Light theme" : "Dark theme"}
    </Button>
  )
}

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col gap-6 p-3">
      <Link
        to="/"
        onClick={onNavigate}
        className="px-2 text-base font-semibold"
      >
        TicketLens
      </Link>
      <NavList onNavigate={onNavigate} />
      <div className="mt-auto flex flex-col gap-2">
        <ThemeToggle />
        <span className="px-2 text-xs text-muted-foreground">
          v0.1.0 · local demo
        </span>
      </div>
    </div>
  )
}

function ProviderBadges() {
  const { data } = useProviderStatus()
  if (!data) return null
  return (
    <div className="hidden items-center gap-1 lg:flex">
      {(["jev", "gpt"] as const).map((provider) => {
        const configured = data[provider].configured
        const Icon = configured ? CircleCheck : CircleX
        return (
          <Badge key={provider} variant="outline" className="gap-1">
            <Icon
              className={cn(
                "size-3",
                configured ? "text-green-600" : "text-muted-foreground",
              )}
              aria-hidden
            />
            {provider === "jev" ? "Jev" : "GPT"}:{" "}
            {configured ? "Configured" : "Not configured"}
          </Badge>
        )
      })}
    </div>
  )
}

function GlobalSearch() {
  const navigate = useNavigate()
  return (
    <form
      role="search"
      className="relative w-full max-w-xs"
      onSubmit={(event) => {
        event.preventDefault()
        const q = String(
          new FormData(event.currentTarget).get("q") ?? "",
        ).trim()
        navigate(q ? `/tickets?q=${encodeURIComponent(q)}` : "/tickets")
      }}
    >
      <Search
        className="absolute top-1/2 left-2 size-4 -translate-y-1/2 text-muted-foreground"
        aria-hidden
      />
      <Input
        name="q"
        type="search"
        placeholder="Search tickets"
        aria-label="Search tickets"
        className="pl-8"
      />
    </form>
  )
}

export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false)
  const title =
    useMatches()
      .map((match) => (match.handle as { title?: string } | undefined)?.title)
      .filter(Boolean)
      .at(-1) ?? "TicketLens"

  useEffect(() => {
    document.title = `${title} · TicketLens`
  }, [title])

  return (
    <div className="min-h-svh bg-background text-foreground md:grid md:grid-cols-[14rem_1fr]">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:m-2 focus:rounded focus:bg-background focus:p-2"
      >
        Skip to content
      </a>
      <aside className="hidden border-r md:block">
        <div className="sticky top-0 h-svh">
          <Sidebar />
        </div>
      </aside>
      <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
        <SheetContent side="left" className="w-64 p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <Sidebar onNavigate={() => setMenuOpen(false)} />
        </SheetContent>
      </Sheet>
      <div className="flex min-w-0 flex-col">
        <header className="flex items-center gap-3 border-b px-4 py-2">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="Open navigation"
            onClick={() => setMenuOpen(true)}
          >
            <Menu aria-hidden />
          </Button>
          <h1 className="mr-auto truncate text-lg font-semibold">{title}</h1>
          <ProviderBadges />
          <GlobalSearch />
          <Button asChild size="sm">
            <Link to="/tickets/new">
              <Plus aria-hidden />
              <span className="hidden sm:inline">New Ticket</span>
              <span className="sr-only sm:hidden">New Ticket</span>
            </Link>
          </Button>
        </header>
        <main id="main" className="min-w-0 flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
