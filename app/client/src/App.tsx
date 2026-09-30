import { createBrowserRouter, RouterProvider, NavLink, Outlet } from 'react-router';
import { useState } from 'react';
import { useTheme } from 'next-themes';
import {
  Button,
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  useIsMobile,
} from '@databricks/appkit-ui/react';
import { Bot, House, Layers, LayoutDashboard, Menu, Moon, Sun } from 'lucide-react';
import { AgentPage } from './pages/agent/AgentPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { HomePage } from './pages/home/HomePage';

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
    isActive
      ? 'bg-primary text-primary-foreground'
      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
  }`;

const mobileNavLinkClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
    isActive
      ? 'bg-primary text-primary-foreground'
      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
  }`;

type NavLinkClassFn = (props: { isActive: boolean }) => string;

function NavLinks({ className, linkClass, onClick }: { className?: string; linkClass: NavLinkClassFn; onClick?: () => void }) {
  return (
    <nav className={className}>
      <NavLink to="/" end className={linkClass} onClick={onClick}>
        <House className="h-4 w-4" />
        Inicio
      </NavLink>
      <NavLink to="/dashboard" className={linkClass} onClick={onClick}>
        <LayoutDashboard className="h-4 w-4" />
        Dashboard
      </NavLink>
      <NavLink to="/agent" className={linkClass} onClick={onClick}>
        <Bot className="h-4 w-4" />
        Agente IA
      </NavLink>
    </nav>
  );
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const isDark = resolvedTheme !== 'light';
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      aria-label={isDark ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'}
    >
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </Button>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <div
        className="h-9 w-9 rounded-lg flex items-center justify-center text-white shadow-sm"
        style={{ background: 'linear-gradient(135deg, #9775fa, #ff6b6b)' }}
      >
        <Layers className="h-5 w-5" />
      </div>
      <div className="leading-tight">
        <h1 className="text-base font-semibold text-foreground">Crypto Lakehouse</h1>
        <p className="text-xs text-muted-foreground hidden sm:block">Databricks · Unity Catalog</p>
      </div>
    </div>
  );
}

function Layout() {
  const isMobile = useIsMobile();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur px-4 md:px-6 py-3 flex items-center gap-6">
        <Brand />
        {/* Desktop nav — hidden below md breakpoint */}
        <NavLinks className="hidden md:flex gap-1" linkClass={navLinkClass} />
        <div className="ml-auto flex items-center gap-1">
          <ThemeToggle />
          {/* Mobile nav — visible below md breakpoint */}
          <div className="md:hidden">
            {/* Gate on isMobile so the portaled sheet can't linger on desktop
                (replaces a set-state-in-effect reset). */}
            <Sheet open={mobileNavOpen && isMobile} onOpenChange={setMobileNavOpen}>
              <Button variant="ghost" size="icon" onClick={() => setMobileNavOpen(true)}>
                <Menu className="h-5 w-5" />
                <span className="sr-only">Abrir navegación</span>
              </Button>
              <SheetContent side="left">
                <SheetHeader>
                  <SheetTitle>Navegación</SheetTitle>
                </SheetHeader>
                <NavLinks className="flex flex-col gap-1 px-4" linkClass={mobileNavLinkClass} onClick={() => setMobileNavOpen(false)} />
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>

      <main className="flex-1 p-4 md:p-6">
        <Outlet />
      </main>
    </div>
  );
}

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/agent', element: <AgentPage /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
