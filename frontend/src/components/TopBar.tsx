import { useAuth } from "../auth/AuthContext";

interface TopBarProps {
  title?: string;
  showSearch?: boolean;
}

export default function TopBar({ title, showSearch = true }: TopBarProps) {
  const { user } = useAuth();

  return (
    <header className="bg-surface/80 backdrop-blur-md border-b border-outline-variant sticky top-0 z-40 flex justify-between items-center h-16 px-margin-desktop">
      {/* Left: title or spacer */}
      {title ? (
        <div className="flex items-center">
          <h2 className="font-title-lg text-title-lg text-on-surface">{title}</h2>
        </div>
      ) : (
        <div className="hidden md:block flex-1" />
      )}

      {/* Right actions */}
      <div className="flex items-center gap-4">
        {/* Search */}
        {showSearch && (
          <div className="hidden lg:flex items-center bg-surface-container rounded-full px-4 py-2 border border-outline-variant/50 focus-within:border-primary focus-within:ring-1 focus-within:ring-primary transition-all w-64">
            <span className="material-symbols-outlined text-on-surface-variant mr-2 text-[20px]">
              search
            </span>
            <input
              className="bg-transparent border-none focus:outline-none focus:ring-0 text-body-sm font-body-sm text-on-surface w-full placeholder:text-on-surface-variant/70"
              placeholder="Search research, courses..."
              type="text"
            />
          </div>
        )}

        {/* Notifications */}
        <button className="relative p-2 rounded-full text-on-surface-variant hover:bg-surface-container-low transition-all">
          <span className="material-symbols-outlined">notifications</span>
          <span className="absolute top-1 right-1 w-2 h-2 bg-error rounded-full" />
        </button>

        {/* Profile avatar */}
        <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center cursor-pointer hover:scale-95 transition-transform duration-200 border border-outline-variant/30 select-none">
          <span className="text-label-md font-label-md uppercase">
            {user?.email?.[0] ?? "U"}
          </span>
        </div>
      </div>
    </header>
  );
}
