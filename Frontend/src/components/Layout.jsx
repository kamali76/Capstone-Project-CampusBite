import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import ErrorBoundary from "./ErrorBoundary";

export default function Layout() {
  return (
    <>
      <Navbar />
      <main className="container">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
    </>
  );
}
