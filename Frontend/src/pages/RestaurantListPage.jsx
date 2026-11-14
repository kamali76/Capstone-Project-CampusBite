import useFetch from "../hooks/useFetch";
import { getRestaurants } from "../api/restaurants";
import Loader from "../components/Loader";
import ErrorMessage from "../components/ErrorMessage";
import RestaurantCard from "../components/RestaurantCard";

export default function RestaurantListPage() {
  const { data: restaurants, loading, error, refetch } = useFetch(getRestaurants, []);

  if (loading && !restaurants) return <Loader text="Loading restaurants..." />;

  if (error) {
    return (
      <>
        <ErrorMessage message={error} />
        <button type="button" onClick={refetch}>
          Try again
        </button>
      </>
    );
  }

  return (
    <div>
      <section className="hero">
        <div className="hero-text">
          <h1>Good food, delivered fast.</h1>
          <p>Pick a restaurant, place your order, and follow it all the way to your door.</p>
        </div>
        <div className="hero-strip" aria-hidden="true">
          <div className="hero-track">
            {[0, 1].map((n) => (
              <span key={n}>🥞 🍕 🍜 ☕ 🍛 🍔 🍟 🥟 🍰 🥤 🍝 🍘 </span>
            ))}
          </div>
        </div>
      </section>
      <h2 className="section-title">Restaurants</h2>
      {restaurants?.length === 0 ? (
        <p>No restaurants available right now.</p>
      ) : (
        <div className="grid">
          {restaurants?.map((r) => (
            <RestaurantCard key={r.id} restaurant={r} />
          ))}
        </div>
      )}
    </div>
  );
}
