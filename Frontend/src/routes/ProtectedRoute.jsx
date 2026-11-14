import { Navigate, Outlet, useLocation } from "react-router-dom";
import useAuth from "../hooks/useAuth";
import { getHomePath } from "../utils/roleHome";

// Only lets in logged-in users whose role is in `allowedRoles`.
// (This is a convenience for the UI - the real checks happen in the FastAPI backend.)
export default function ProtectedRoute({ allowedRoles }) {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    return <Navigate to={getHomePath(user?.role)} replace />;
  }
  return <Outlet />;
}
