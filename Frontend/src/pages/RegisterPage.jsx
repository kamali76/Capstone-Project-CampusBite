import { useReducer, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import useAuth from "../hooks/useAuth";
import ErrorMessage from "../components/ErrorMessage";
import { getErrorMessage } from "../utils/errors";
import { ROLES } from "../utils/constants";

const initialState = {
  name: "",
  email: "",
  password: "",
  phone: "",
  role: ROLES.CUSTOMER,
  restaurant_name: "",
};

function formReducer(state, action) {
  switch (action.type) {
    case "CHANGE":
      return { ...state, [action.field]: action.value };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, dispatch] = useReducer(formReducer, initialState);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) =>
    dispatch({ type: "CHANGE", field: e.target.name, value: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = {
        name: form.name,
        email: form.email.trim(),
        password: form.password,
        role: form.role,
        phone: form.phone.trim() || null,
        restaurant_name:
          form.role === ROLES.OWNER ? form.restaurant_name.trim() || null : null,
      };
      await register(payload);
      dispatch({ type: "RESET" });
      navigate("/login", { state: { registeredEmail: payload.email } });
    } catch (err) {
      setError(getErrorMessage(err));
      setLoading(false);
    }
  };

  return (
    <div className="auth-card">
      <h2>Create your account</h2>
      <ErrorMessage message={error} />
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Name</label>
          <input id="name" name="name" value={form.name} onChange={handleChange} minLength={2} required />
        </div>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input id="email" name="email" type="email" value={form.email} onChange={handleChange} required />
        </div>
        <div className="form-group">
          <label htmlFor="phone">Phone (optional)</label>
          <input id="phone" name="phone" type="tel" value={form.phone} onChange={handleChange} maxLength={20} />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            minLength={6}
            value={form.password}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="role">I am a</label>
          <select id="role" name="role" value={form.role} onChange={handleChange}>
            <option value={ROLES.CUSTOMER}>Customer</option>
            <option value={ROLES.OWNER}>Restaurant Owner</option>
            <option value={ROLES.DELIVERY}>Delivery Partner</option>
          </select>
        </div>
        {form.role === ROLES.OWNER && (
          <div className="form-group">
            <label htmlFor="restaurant_name">Restaurant name</label>
            <input
              id="restaurant_name"
              name="restaurant_name"
              value={form.restaurant_name}
              onChange={handleChange}
              maxLength={120}
              placeholder="e.g. Spice Route"
            />
          </div>
        )}
        <button type="submit" disabled={loading}>
          {loading ? "Creating account..." : "Register"}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}
