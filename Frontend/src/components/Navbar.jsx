import { NavLink, useNavigate } from "react-router-dom";
import useAuth from "../hooks/useAuth";
import useCart from "../hooks/useCart";
import { ROLES } from "../utils/constants";

const NAV_LINKS = {
  [ROLES.CUSTOMER]: [
    { to: "/restaurants", label: "Restaurants" },
    { to: "/cart", label: "Cart", isCart: true },
    { to: "/orders", label: "My Orders" },
    { to: "/ai-insights", label: "AI Insights" },
  ],
  [ROLES.OWNER]: [
    { to: "/owner/dashboard", label: "Dashboard" },
    { to: "/owner/orders", label: "Orders" },
    { to: "/owner/menu", label: "Menu" },
  ],
  [ROLES.DELIVERY]: [{ to: "/delivery/dashboard", label: "Deliveries" }],
};

export default function Navbar() {
  const { user, logout } = useAuth();
  const { totalItems } = useCart();
  const navigate = useNavigate();
  const links = NAV_LINKS[user?.role] || [];

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <span className="navbar-brand">
        <span className="brand-mark" aria-hidden="true">🍴</span>CampusBite
      </span>
      <div className="navbar-links">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
          >
            {link.label}
            {link.isCart && totalItems > 0 && <span key={totalItems} className="cart-count">{totalItems}</span>}
          </NavLink>
        ))}
      </div>
      <div className="navbar-user">
        <span className="navbar-name">{user?.name}</span>
        <button type="button" onClick={handleLogout}>
          Log out
        </button>
      </div>
    </nav>
  );
}
