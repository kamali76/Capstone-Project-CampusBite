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
      <h2>Restaurants</h2>
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
