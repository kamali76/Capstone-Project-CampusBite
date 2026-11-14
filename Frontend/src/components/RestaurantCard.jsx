import { Link } from "react-router-dom";
import { cuisineLook } from "../utils/foodEmoji";

export default function RestaurantCard({ restaurant }) {
  const { emoji, tone } = cuisineLook(restaurant.cuisine, restaurant.id);
  return (
    <Link to={`/restaurants/${restaurant.id}`} className="card restaurant-card">
      <div className={`cover cover-${tone}`} aria-hidden="true">
        <span className="cover-emoji">{emoji}</span>
        {restaurant.rating ? (
          <span className="rating-chip">★ {restaurant.rating}</span>
        ) : (
          <span className="rating-chip new">New</span>
        )}
      </div>
      <div className="restaurant-card-body">
        <h3>{restaurant.name}</h3>
        {restaurant.cuisine && <p className="muted">{restaurant.cuisine}</p>}
        {restaurant.description && <p className="restaurant-desc">{restaurant.description}</p>}
        {restaurant.address && <p className="muted">📍 {restaurant.address}</p>}
        <p className="muted">
          {restaurant.rating ? `${restaurant.review_count} review${restaurant.review_count === 1 ? "" : "s"}` : "No reviews yet"}
        </p>
      </div>
    </Link>
  );
}
