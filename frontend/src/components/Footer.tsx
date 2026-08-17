import { Link } from "react-router-dom";
import { Leaf, Github, Linkedin } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-muted/30 border-t pt-16 pb-8" role="contentinfo">
      <div className="container mx-auto px-4 md:px-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          <div>
            <Link
              to="/"
              className="flex items-center gap-2 group mb-4 focus:outline-none focus:ring-2 focus:ring-ring rounded-lg w-fit"
            >
              <div className="bg-primary text-primary-foreground p-1.5 rounded-lg">
                <Leaf size={24} aria-hidden="true" />
              </div>
              <span className="font-bold text-xl tracking-tight text-foreground">
                Waste-IQ
              </span>
            </Link>
            <p className="text-muted-foreground text-sm leading-relaxed mb-6">
              Revolutionizing waste management with smart scheduling, real-time
              tracking, and a digital marketplace for recyclables.
            </p>
            <div className="flex items-center gap-4 text-muted-foreground">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="GitHub"
                className="hover:text-primary transition-colors focus:outline-none focus:ring-2 focus:ring-ring rounded"
              >
                <Github size={20} />
              </a>
              <a
                href="https://linkedin.com"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="LinkedIn"
                className="hover:text-primary transition-colors focus:outline-none focus:ring-2 focus:ring-ring rounded"
              >
                <Linkedin size={20} />
              </a>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-foreground mb-4">Features</h3>
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li>
                <Link to="/features" className="hover:text-primary transition-colors">
                  Platform Features
                </Link>
              </li>
              <li>
                <Link to="/#how-it-works" className="hover:text-primary transition-colors">
                  How it Works
                </Link>
              </li>
              <li>
                <Link to="/register" className="hover:text-primary transition-colors">
                  Get Started
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-foreground mb-4">Company</h3>
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li>
                <Link to="/about" className="hover:text-primary transition-colors">
                  About Us
                </Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-primary transition-colors">
                  Contact
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-foreground mb-4">Resources</h3>
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li>Privacy Policy</li>
              <li>Terms of Service</li>
              <li>Documentation</li>
            </ul>
          </div>
        </div>

        <div className="border-t pt-8 flex flex-col md:flex-row items-center justify-between text-sm text-muted-foreground gap-4">
          <p>Copyright {new Date().getFullYear()} Waste-IQ. All rights reserved.</p>
          <p>Built for a cleaner planet.</p>
        </div>
      </div>
    </footer>
  );
}
