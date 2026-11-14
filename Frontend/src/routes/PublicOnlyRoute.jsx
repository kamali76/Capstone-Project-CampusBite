import { Navigate, Outlet } from "react-router-dom";
import useAuth from "../hooks/useAuth";
import { getHomePath } from "../utils/roleHome";

// Login/register are for logged-out users only
export default function PublicOnlyRoute() {
  const { isAuthenticated, user } = useAuth();
  if (isAuthenticated) {
    return <Navigate to={getHomePath(user?.role)} replace />;
  }
  return <Outlet />;
}
