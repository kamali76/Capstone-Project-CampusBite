import { Link } from "react-router-dom";

export default function RestaurantCard({ restaurant }) {
  return (
    <Link to={`/restaurants/${restaurant.id}`} className="card restaurant-card">
      <h3>{restaurant.name}</h3>
      {restaurant.cuisine && <p className="muted">{restaurant.cuisine}</p>}
      {restaurant.description && <p>{restaurant.description}</p>}
      {restaurant.address && <p className="muted">📍 {restaurant.address}</p>}
      <p>
        {restaurant.rating ? (
          <>
            ⭐ {restaurant.rating} <span className="muted">({restaurant.review_count})</span>
          </>
        ) : (
          <span className="muted">New · no reviews yet</span>
        )}
      </p>
    </Link>
  );
}
