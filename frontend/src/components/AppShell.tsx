import { Outlet } from "react-router-dom";
import SideNav from "./SideNav";

export default function AppShell() {
  return (
    <div className="flex min-h-screen bg-background">
      {/* Fixed side navigation */}
      <SideNav />

      {/* Main content area offset by sidebar width */}
      <div className="flex-1 flex flex-col md:ml-64 min-h-screen">
        <Outlet />
      </div>
    </div>
  );
}
