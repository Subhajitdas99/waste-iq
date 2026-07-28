import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, X, Leaf, Sun, Moon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "./ui/button";
import { useTheme } from "../context/ThemeContext";
import { useAuth } from "../context/AuthContext";

const navLinks = [
  { name: "Home", path: "/" },
  { name: "Features", path: "/features" },
  { name: "About", path: "/about" },
  { name: "Contact", path: "/contact" },
];

export function Navigation() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();
  const { user, token } = useAuth();

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  const handleNavClick = (path: string) => {
    if (path.includes("#")) {
      const [route, hash] = path.split("#");
      if (location.pathname === route || (route === "/" && location.pathname === "/")) {
        document.getElementById(hash)?.scrollIntoView({ behavior: "smooth" });
      } else {
        navigate(`${route}#${hash}`);
      }
    }
    setMobileMenuOpen(false);
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 border-b ${
        isScrolled
          ? "bg-background/80 backdrop-blur-md border-border py-3 shadow-sm"
          : "bg-transparent border-transparent py-5"
      }`}
    >
      <div className="container mx-auto px-4 md:px-6 flex items-center justify-between">
        <Link
          to="/"
          className="flex items-center gap-2 group focus:outline-none focus:ring-2 focus:ring-ring rounded-lg"
          aria-label="Waste-IQ home"
        >
          <div className="bg-primary text-primary-foreground p-1.5 rounded-lg group-hover:bg-primary/90 transition-colors">
            <Leaf size={24} aria-hidden="true" />
          </div>
          <span className="font-bold text-xl tracking-tight text-foreground">
            Waste-IQ
          </span>
        </Link>

        <nav
          className="hidden md:flex items-center gap-8"
          aria-label="Main navigation"
        >
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`text-sm font-medium transition-colors hover:text-primary focus:outline-none focus:ring-2 focus:ring-ring rounded px-1 py-0.5 ${
                isActive(link.path) ? "text-primary" : "text-muted-foreground"
              }`}
            >
              {link.name}
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className="p-2 text-muted-foreground hover:text-foreground transition-colors rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? <Sun size={20} /> : <Moon size={20} />}
          </button>

          {token && user ? (
            <Link to={user.role === "collector" ? "/collector/profile" : "/dashboard"}>
              <Button className="font-medium">Dashboard</Button>
            </Link>
          ) : (
            <>
              <Link to="/login">
                <Button variant="ghost" className="font-medium">
                  Log in
                </Button>
              </Link>
              <Link to="/register">
                <Button className="font-medium">Sign up</Button>
              </Link>
            </>
          )}
        </div>

        <button
          className="md:hidden p-2 text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-full left-0 w-full bg-background/95 backdrop-blur-md border-b shadow-lg md:hidden flex flex-col p-4 gap-2"
            role="dialog"
            aria-label="Mobile navigation"
          >
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => handleNavClick(link.path)}
                className={`text-lg font-medium p-3 rounded-md focus:outline-none focus:ring-2 focus:ring-ring ${
                  isActive(link.path)
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted"
                }`}
              >
                {link.name}
              </Link>
            ))}

            <div className="h-px bg-border my-2" />

            <div className="flex flex-col gap-2">
              {token && user ? (
                <Link
                  to={user.role === "collector" ? "/collector/profile" : "/dashboard"}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Button className="w-full justify-center">Dashboard</Button>
                </Link>
              ) : (
                <>
                  <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                    <Button variant="outline" className="w-full justify-center">
                      Log in
                    </Button>
                  </Link>
                  <Link to="/register" onClick={() => setMobileMenuOpen(false)}>
                    <Button className="w-full justify-center">Sign up</Button>
                  </Link>
                </>
              )}
            </div>

            <button
              onClick={toggleTheme}
              className="mt-2 p-3 text-sm font-medium text-muted-foreground text-center rounded-md hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring flex items-center justify-center gap-2"
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
              {theme === "dark" ? "Light Mode" : "Dark Mode"}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
