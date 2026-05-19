import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useNavigate } from "react-router-dom";

type NavItem = {
  to: string;
  icon: string;
  label: string;
  fill?: boolean;
};

const mainNavItems: NavItem[] = [
  { to: "/dashboard", icon: "dashboard", label: "Dashboard" },
  { to: "/chat", icon: "chat_spark", label: "Find Thesis" },
  { to: "/chairs", icon: "explore", label: "Lehrstuhl-Explorer" },
  { to: "/proposals", icon: "description", label: "My Proposals" },
];

const footerNavItems: NavItem[] = [
  { to: "/settings", icon: "settings", label: "Settings" },
  { to: "/help", icon: "help", label: "Help" },
];

export default function SideNav() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <nav className="bg-surface h-screen w-64 fixed left-0 top-0 border-r border-outline-variant flex flex-col py-stack-lg z-50">
      {/* Header */}
      <div className="px-6 mb-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center shrink-0">
            <span
              className="material-symbols-outlined text-on-primary"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              school
            </span>
          </div>
          <div>
            <h1 className="text-headline-md font-headline-md font-bold text-primary tracking-tight">
              ScholarAI
            </h1>
            <p className="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mt-1">
              Academic Excellence
            </p>
          </div>
        </div>
      </div>

      {/* Main Navigation */}
      <div className="flex-1 overflow-y-auto px-4 flex flex-col gap-1">
        {mainNavItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              isActive
                ? "flex items-center gap-3 px-4 py-3 rounded-lg text-primary font-bold border-r-2 border-primary bg-surface-container-low transition-colors group"
                : "flex items-center gap-3 px-4 py-3 rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-colors group"
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className="material-symbols-outlined"
                  style={
                    isActive
                      ? { fontVariationSettings: "'FILL' 1" }
                      : undefined
                  }
                >
                  {item.icon}
                </span>
                <span className="font-label-md text-label-md">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>

      {/* Footer Navigation */}
      <div className="px-4 mt-auto pt-6 border-t border-outline-variant/30 flex flex-col gap-1">
        {footerNavItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className="flex items-center gap-3 px-4 py-3 rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-colors group"
          >
            <span className="material-symbols-outlined">{item.icon}</span>
            <span className="font-label-md text-label-md">{item.label}</span>
          </NavLink>
        ))}
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-colors w-full text-left"
        >
          <span className="material-symbols-outlined">logout</span>
          <span className="font-label-md text-label-md">Log out</span>
        </button>
      </div>
    </nav>
  );
}
