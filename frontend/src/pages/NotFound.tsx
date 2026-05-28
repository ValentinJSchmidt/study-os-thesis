import { useNavigate } from "react-router-dom";

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="max-w-md w-full text-center flex flex-col items-center gap-6">
        <div className="w-16 h-16 rounded-2xl bg-secondary-container flex items-center justify-center">
          <span
            className="material-symbols-outlined text-on-secondary-container text-3xl"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            search_off
          </span>
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-display-small font-bold text-on-surface-variant">404</p>
          <h1 className="text-title-large text-on-surface font-semibold">
            Page not found
          </h1>
          <p className="text-body-medium text-on-surface-variant">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        <button
          onClick={() => navigate("/dashboard")}
          className="px-6 py-2.5 rounded-full bg-primary text-on-primary text-label-large font-medium hover:opacity-90 transition-opacity"
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}
