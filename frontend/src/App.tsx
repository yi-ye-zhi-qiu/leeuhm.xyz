import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider, useTheme } from "./theme-context";

const queryClient = new QueryClient();

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  return (
    <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      toggle theme
    </button>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="leeuhmxyz-ui-theme">
        <ThemeToggle />
        <div>Hello world!</div>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
