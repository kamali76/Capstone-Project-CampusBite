import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import useAuth from "../hooks/useAuth";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import { getErrorMessage } from "../utils/errors";
import { getHomePath } from "../utils/roleHome";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // After registering we arrive here with a success note and the email pre-filled
  const justRegistered = location.state?.registeredEmail;

  const [form, setForm] = useState({ email: justRegistered || "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const loggedInUser = await login(form.email.trim(), form.password);
      // Go back to the page they tried to open, or their role's home page
      const destination = location.state?.from?.pathname || getHomePath(loggedInUser.role);
      navigate(destination, { replace: true });
    } catch (err) {
      setError(getErrorMessage(err));
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-emojis" aria-hidden="true">
        {["🍕", "🍜", "☕", "🍔", "🥞", "🍰", "🍛", "🥤"].map((e, i) => (
          <span key={i} className={`float float-${i + 1}`}>{e}</span>
        ))}
      </div>
    <div className="auth-card">
      <h2>Log in to CampusBite</h2>
      <p className="muted auth-sub">Order food, manage your restaurant, or deliver orders.</p>
      {justRegistered && <SuccessMessage message="Account created! Please log in." />}
      <ErrorMessage message={error} />
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={form.password}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? "Logging in..." : "Log in"}
        </button>
      </form>
      <p>
        New here? <Link to="/register">Create an account</Link>
      </p>
    </div>
    </div>
  );
}
