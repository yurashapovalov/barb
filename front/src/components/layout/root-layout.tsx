import { Outlet } from "react-router-dom";

export function RootLayout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
