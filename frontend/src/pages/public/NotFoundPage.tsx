import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { SeoHead } from "@/components/seo/SeoHead";
import { useAuth } from "@/context/AuthContext";
import { getRoleHomePath, getRolePortalLabel } from "@/lib/portal";

export function NotFoundPage() {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center px-4">
      <SeoHead
        title="404 - Page Not Found"
        description="The page you are looking for could not be found."
        path="/404"
      />
      <h1 className="text-9xl font-extrabold text-primary/20 mb-4 tracking-tighter">
        404
      </h1>
      <h2 className="text-3xl font-bold mb-4">Page Not Found</h2>
      <p className="text-muted-foreground max-w-md mx-auto mb-8">
        Sorry, we couldn&apos;t find the page you&apos;re looking for. It might
        have been moved or deleted.
      </p>
      <Link to="/">
        <Button size="lg" className="rounded-full">
          Return Home
        </Button>
      </Link>
    </div>
  );
}

export function UnauthorizedPage() {
  const { user, isAuthenticated } = useAuth();
  const roleHomePath = getRoleHomePath(user?.role);
  const roleLabel = getRolePortalLabel(user?.role);

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center px-4">
      <SeoHead
        title="403 - Unauthorized"
        description="You do not have permission to access this page."
        path="/unauthorized"
      />
      <div
        className="w-20 h-20 bg-destructive/10 text-destructive rounded-full flex items-center justify-center mb-6"
        aria-hidden="true"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
          className="w-10 h-10"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
          />
        </svg>
      </div>
      <h2 className="text-3xl font-bold mb-4">Access Denied</h2>
      <p className="text-muted-foreground max-w-md mx-auto mb-8">
        You do not have permission to access this page. Please contact an
        administrator if you believe this is an error.
      </p>
      <div className="flex gap-4">
        <Link to="/">
          <Button variant="outline" size="lg" className="rounded-full">
            Return Home
          </Button>
        </Link>
        {isAuthenticated ? (
          <Link to={roleHomePath}>
            <Button size="lg" className="rounded-full">
              Open {roleLabel}
            </Button>
          </Link>
        ) : (
          <Link to="/login">
            <Button size="lg" className="rounded-full">
              Sign In
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
}
