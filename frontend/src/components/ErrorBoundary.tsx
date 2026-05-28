import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Catches unhandled JS runtime errors anywhere in the component tree
 * and renders a clean error screen instead of a blank page.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="max-w-md w-full text-center flex flex-col items-center gap-6">
          <div className="w-16 h-16 rounded-2xl bg-error-container flex items-center justify-center">
            <span
              className="material-symbols-outlined text-on-error-container text-3xl"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              error
            </span>
          </div>

          <div className="flex flex-col gap-2">
            <h1 className="text-title-large text-on-surface font-semibold">
              Something went wrong
            </h1>
            <p className="text-body-medium text-on-surface-variant">
              An unexpected error occurred. Please reload the page.
            </p>
            {error.message && (
              <p className="text-label-small text-on-surface-variant font-mono bg-surface-variant rounded-lg px-3 py-2 mt-1">
                {error.message}
              </p>
            )}
          </div>

          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2.5 rounded-full bg-primary text-on-primary text-label-large font-medium hover:opacity-90 transition-opacity"
          >
            Reload page
          </button>
        </div>
      </div>
    );
  }
}
