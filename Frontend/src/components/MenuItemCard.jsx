import { formatPrice } from "../utils/format";
import { dishEmoji } from "../utils/foodEmoji";

export default function MenuItemCard({ item, inCartQty = 0, onAdd }) {
  return (
    <div className={`card menu-item ${item.is_available ? "" : "unavailable"}`}>
      <div className="menu-item-top">
        <span className="dish-emoji" aria-hidden="true">
          {dishEmoji(item.name, item.category)}
        </span>
        <div>
          <h4>{item.name}</h4>
          {item.description && <p className="muted">{item.description}</p>}
        </div>
      </div>
      <div className="menu-item-footer">
        <strong className="price">{formatPrice(item.price)}</strong>
        {item.is_available ? (
          <button type="button" className={inCartQty > 0 ? "in-cart" : ""} onClick={() => onAdd(item)}>
            {inCartQty > 0 ? `Add more (${inCartQty})` : "Add to cart"}
          </button>
        ) : (
          <span className="badge">Unavailable</span>
        )}
      </div>
    </div>
  );
}
