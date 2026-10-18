import { Link, Outlet, createRootRoute } from "@tanstack/react-router";
import { ThemeProvider, useTheme } from "../theme-context";

export const Route = createRootRoute({
  component: RootComponent,
});

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  return (
    <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      theme: {theme}
    </button>
  );
}

function RootComponent() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="espresso-gg-ui-theme">
      <nav>
        <Link to="/">home</Link>
        <Link to="/leaderboard" search={{ region: "na1", pageIndex: "1" }}>
          leaderboard
        </Link>
        <ThemeToggle />
      </nav>
      <Outlet />
    </ThemeProvider>
  );
}
