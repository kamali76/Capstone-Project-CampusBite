import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import RestaurantListPage from "./pages/RestaurantListPage";
import RestaurantMenuPage from "./pages/RestaurantMenuPage";
import CartPage from "./pages/CartPage";
import CustomerOrdersPage from "./pages/CustomerOrdersPage";
import AIInsightsPage from "./pages/AIInsightsPage";
import OwnerDashboardPage from "./pages/OwnerDashboardPage";
import OwnerOrdersPage from "./pages/OwnerOrdersPage";
import MenuManagementPage from "./pages/MenuManagementPage";
import DeliveryDashboardPage from "./pages/DeliveryDashboardPage";
import NotFoundPage from "./pages/NotFoundPage";
import Layout from "./components/Layout";
import ProtectedRoute from "./routes/ProtectedRoute";
import PublicOnlyRoute from "./routes/PublicOnlyRoute";
import CartProvider from "./context/CartProvider";
import useAuth from "./hooks/useAuth";
import { ROLES } from "./utils/constants";
import { getHomePath } from "./utils/roleHome";

// "/" sends people to the right place based on login state and role
function RootRedirect() {
  const { isAuthenticated, user } = useAuth();
  return <Navigate to={isAuthenticated ? getHomePath(user?.role) : "/login"} replace />;
}

export default function App() {
  const { user } = useAuth();

  return (
    // key={user.id}: every user gets a fresh cart (and their own saved cart) when they log in
    <CartProvider key={user?.id ?? "guest"} userId={user?.id}>
      <Routes>
        <Route path="/" element={<RootRedirect />} />

        {/* Only for logged-out users */}
        <Route element={<PublicOnlyRoute />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>

        {/* Customer pages */}
        <Route element={<ProtectedRoute allowedRoles={[ROLES.CUSTOMER]} />}>
          <Route element={<Layout />}>
            <Route path="/restaurants" element={<RestaurantListPage />} />
            <Route path="/restaurants/:id" element={<RestaurantMenuPage />} />
            <Route path="/cart" element={<CartPage />} />
            <Route path="/orders" element={<CustomerOrdersPage />} />
            <Route path="/ai-insights" element={<AIInsightsPage />} />
          </Route>
        </Route>

        {/* Restaurant owner pages */}
        <Route element={<ProtectedRoute allowedRoles={[ROLES.OWNER]} />}>
          <Route element={<Layout />}>
            <Route path="/owner/dashboard" element={<OwnerDashboardPage />} />
            <Route path="/owner/orders" element={<OwnerOrdersPage />} />
            <Route path="/owner/menu" element={<MenuManagementPage />} />
          </Route>
        </Route>

        {/* Delivery partner pages */}
        <Route element={<ProtectedRoute allowedRoles={[ROLES.DELIVERY]} />}>
          <Route element={<Layout />}>
            <Route path="/delivery/dashboard" element={<DeliveryDashboardPage />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </CartProvider>
  );
}
