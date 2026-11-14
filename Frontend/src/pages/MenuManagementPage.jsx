import { useMemo, useState } from "react";
import useFetch from "../hooks/useFetch";
import {
  createMenuItem,
  deleteMenuItem,
  getMyRestaurant,
  listMenuItems,
  setAvailability,
  updateMenuItem,
  updateRestaurant,
} from "../api/owner";
import Loader from "../components/Loader";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import { getErrorMessage } from "../utils/errors";
import { formatPrice } from "../utils/format";

const emptyDish = { name: "", category: "", description: "", price: "", is_available: true };

// Restaurant profile editor (name, cuisine, address, description)
function RestaurantProfile({ restaurant, onSaved, onError }) {
  const [form, setForm] = useState({
    name: restaurant.name,
    cuisine: restaurant.cuisine,
    address: restaurant.address,
    description: restaurant.description,
  });
  const [saving, setSaving] = useState(false);

  const handleChange = (e) => setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await updateRestaurant(form);
      onSaved("Restaurant details saved.");
    } catch (err) {
      onError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <details className="card">
      <summary>Restaurant details · {restaurant.name}</summary>
      <form onSubmit={handleSubmit} className="profile-form">
        <div className="form-group">
          <label htmlFor="r-name">Name</label>
          <input id="r-name" name="name" value={form.name} onChange={handleChange} minLength={2} required />
        </div>
        <div className="form-group">
          <label htmlFor="r-cuisine">Cuisine</label>
          <input id="r-cuisine" name="cuisine" value={form.cuisine} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label htmlFor="r-address">Address</label>
          <input id="r-address" name="address" value={form.address} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label htmlFor="r-description">Description</label>
          <input id="r-description" name="description" value={form.description} onChange={handleChange} />
        </div>
        <button type="submit" disabled={saving}>
          {saving ? "Saving..." : "Save details"}
        </button>
      </form>
    </details>
  );
}

export default function MenuManagementPage() {
  const menu = useFetch(listMenuItems, []);
  const restaurant = useFetch(getMyRestaurant, []);

  const [form, setForm] = useState(emptyDish);
  const [editingId, setEditingId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const grouped = useMemo(() => {
    const groups = {};
    (menu.data || []).forEach((item) => {
      if (!groups[item.category]) groups[item.category] = [];
      groups[item.category].push(item);
    });
    return groups;
  }, [menu.data]);

  const handleChange = (e) => {
    const { name, type, value, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
  };

  const resetForm = () => {
    setForm(emptyDish);
    setEditingId(null);
  };

  const startEdit = (item) => {
    setEditingId(item.id);
    setForm({
      name: item.name,
      category: item.category,
      description: item.description,
      price: String(item.price),
      is_available: item.is_available,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const notify = (message) => {
    setError("");
    setSuccess(message);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);
    const payload = {
      name: form.name.trim(),
      category: form.category.trim() || "General",
      description: form.description.trim(),
      price: Number(form.price),
      is_available: form.is_available,
    };
    try {
      if (editingId) {
        await updateMenuItem(editingId, payload);
        notify(`"${payload.name}" updated.`);
      } else {
        await createMenuItem(payload);
        notify(`"${payload.name}" added to your menu.`);
      }
      resetForm();
      menu.refetch();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const runOnItem = async (item, action, message) => {
    setError("");
    setSuccess("");
    setBusyId(item.id);
    try {
      await action();
      notify(message);
      if (editingId === item.id) resetForm();
      menu.refetch();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  const toggleAvailability = (item) =>
    runOnItem(
      item,
      () => setAvailability(item.id, !item.is_available),
      `"${item.name}" marked ${item.is_available ? "unavailable" : "available"}.`
    );

  const handleDelete = (item) => {
    if (!window.confirm(`Delete "${item.name}" from your menu? Past orders are not affected.`)) return;
    runOnItem(item, () => deleteMenuItem(item.id), `"${item.name}" deleted.`);
  };

  const categories = Object.keys(grouped);

  return (
    <div>
      <h2>Menu management</h2>
      <SuccessMessage message={success} />
      <ErrorMessage message={error || menu.error || restaurant.error} />

      {restaurant.data && (
        <RestaurantProfile
          key={restaurant.data.id}
          restaurant={restaurant.data}
          onSaved={(msg) => {
            notify(msg);
            restaurant.refetch();
          }}
          onError={setError}
        />
      )}

      <form className="card dish-form" onSubmit={handleSubmit}>
        <h3>{editingId ? "Edit dish" : "Add a new dish"}</h3>
        <div className="dish-form-grid">
          <div className="form-group">
            <label htmlFor="d-name">Dish name</label>
            <input id="d-name" name="name" value={form.name} onChange={handleChange} minLength={2} maxLength={100} required />
          </div>
          <div className="form-group">
            <label htmlFor="d-category">Category</label>
            <input
              id="d-category"
              name="category"
              value={form.category}
              onChange={handleChange}
              placeholder="e.g. Snacks"
              maxLength={50}
              list="category-options"
            />
            <datalist id="category-options">
              {categories.map((c) => (
                <option key={c} value={c} />
              ))}
            </datalist>
          </div>
          <div className="form-group">
            <label htmlFor="d-price">Price (₹)</label>
            <input id="d-price" name="price" type="number" min="1" step="0.5" value={form.price} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label htmlFor="d-description">Description</label>
            <input id="d-description" name="description" value={form.description} onChange={handleChange} maxLength={500} />
          </div>
        </div>
        <label className="checkbox-row">
          <input type="checkbox" name="is_available" checked={form.is_available} onChange={handleChange} />
          Available to order
        </label>
        <div className="checkout-actions">
          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : editingId ? "Save changes" : "Add dish"}
          </button>
          {editingId && (
            <button type="button" className="secondary" onClick={resetForm}>
              Cancel edit
            </button>
          )}
        </div>
      </form>

      {menu.loading && !menu.data && <Loader text="Loading your menu..." />}
      {menu.data && categories.length === 0 && <p>Your menu is empty. Add your first dish above.</p>}

      {categories.map((category) => (
        <section key={category}>
          <h3>{category}</h3>
          <div className="grid">
            {grouped[category].map((item) => (
              <div key={item.id} className={`card menu-item ${item.is_available ? "" : "unavailable"}`}>
                <div>
                  <h4>{item.name}</h4>
                  {item.description && <p className="muted">{item.description}</p>}
                  <p>
                    <strong>{formatPrice(item.price)}</strong>{" "}
                    {!item.is_available && <span className="badge">Unavailable</span>}
                  </p>
                </div>
                <div className="menu-actions">
                  <button type="button" className="secondary" disabled={busyId === item.id} onClick={() => startEdit(item)}>
                    Edit
                  </button>
                  <button type="button" className="secondary" disabled={busyId === item.id} onClick={() => toggleAvailability(item)}>
                    {item.is_available ? "Mark unavailable" : "Mark available"}
                  </button>
                  <button type="button" className="danger" disabled={busyId === item.id} onClick={() => handleDelete(item)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
