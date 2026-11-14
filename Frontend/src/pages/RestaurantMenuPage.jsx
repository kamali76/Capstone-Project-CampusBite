import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import useFetch from "../hooks/useFetch";
import useDebounce from "../hooks/useDebounce";
import useCart from "../hooks/useCart";
import { getRestaurant, getMenu } from "../api/restaurants";
import Loader from "../components/Loader";
import ErrorMessage from "../components/ErrorMessage";
import MenuItemCard from "../components/MenuItemCard";

export default function RestaurantMenuPage() {
  const { id } = useParams();
  const cart = useCart();

  // Filter inputs (update instantly as the user types)
  const [search, setSearch] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");

  // Debounced values (update 400ms after the user stops typing)
  const debouncedSearch = useDebounce(search, 400);
  const debouncedMin = useDebounce(minPrice, 400);
  const debouncedMax = useDebounce(maxPrice, 400);

  const restaurantReq = useFetch(() => getRestaurant(id), [id]);
  const menuReq = useFetch(
    () => getMenu(id, { search: debouncedSearch, minPrice: debouncedMin, maxPrice: debouncedMax }),
    [id, debouncedSearch, debouncedMin, debouncedMax]
  );

  // Group dishes by category; recomputed only when the menu data changes
  const groupedMenu = useMemo(() => {
    const groups = {};
    (menuReq.data || []).forEach((item) => {
      if (!groups[item.category]) groups[item.category] = [];
      groups[item.category].push(item);
    });
    return groups;
  }, [menuReq.data]);

  const quantityInCart = (itemId) =>
    cart.restaurant?.id === Number(id) ? cart.items.find((i) => i.id === itemId)?.quantity || 0 : 0;

  const handleAdd = (item) => {
    const restaurant = restaurantReq.data;
    // A cart can only hold dishes from one restaurant
    if (cart.restaurant && cart.restaurant.id !== restaurant.id && cart.items.length > 0) {
      const ok = window.confirm(
        `Your cart has items from ${cart.restaurant.name}. Start a new cart with ${restaurant.name}?`
      );
      if (!ok) return;
    }
    cart.addItem({ id: restaurant.id, name: restaurant.name }, item);
  };

  const clearFilters = () => {
    setSearch("");
    setMinPrice("");
    setMaxPrice("");
  };

  if (restaurantReq.loading && !restaurantReq.data) return <Loader text="Loading restaurant..." />;
  if (restaurantReq.error) {
    return (
      <>
        <ErrorMessage message={restaurantReq.error} />
        <Link to="/restaurants">← Back to restaurants</Link>
      </>
    );
  }

  const restaurant = restaurantReq.data;
  const categories = Object.keys(groupedMenu);
  const cartHere = cart.restaurant?.id === restaurant.id ? cart.totalItems : 0;

  return (
    <div>
      <Link to="/restaurants">← Back to restaurants</Link>
      <h2>{restaurant.name}</h2>
      <p className="muted">
        {[restaurant.cuisine, restaurant.address && `📍 ${restaurant.address}`, restaurant.rating && `⭐ ${restaurant.rating}`]
          .filter(Boolean)
          .join(" · ")}
      </p>

      {cartHere > 0 && (
        <p className="cart-banner">
          🛒 {cartHere} item{cartHere > 1 ? "s" : ""} in your cart · <Link to="/cart">View cart</Link>
        </p>
      )}

      <div className="filters">
        <input
          type="search"
          placeholder="Search dishes..."
          aria-label="Search dishes"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <input
          type="number"
          min="0"
          placeholder="Min ₹"
          aria-label="Minimum price"
          value={minPrice}
          onChange={(e) => setMinPrice(e.target.value)}
        />
        <input
          type="number"
          min="0"
          placeholder="Max ₹"
          aria-label="Maximum price"
          value={maxPrice}
          onChange={(e) => setMaxPrice(e.target.value)}
        />
        <button type="button" className="secondary" onClick={clearFilters}>
          Clear
        </button>
      </div>

      {menuReq.loading && <Loader text="Loading menu..." />}
      <ErrorMessage message={menuReq.error} />

      {!menuReq.loading && !menuReq.error && categories.length === 0 && (
        <p>No dishes match your filters.</p>
      )}

      {categories.map((category) => (
        <section key={category}>
          <h3>{category}</h3>
          <div className="grid">
            {groupedMenu[category].map((item) => (
              <MenuItemCard
                key={item.id}
                item={item}
                inCartQty={quantityInCart(item.id)}
                onAdd={handleAdd}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
