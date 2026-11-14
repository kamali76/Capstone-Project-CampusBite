import { formatPrice } from "../utils/format";

export default function MenuItemCard({ item, inCartQty = 0, onAdd }) {
  return (
    <div className={`card menu-item ${item.is_available ? "" : "unavailable"}`}>
      <div>
        <h4>{item.name}</h4>
        {item.description && <p className="muted">{item.description}</p>}
      </div>
      <div className="menu-item-footer">
        <strong>{formatPrice(item.price)}</strong>
        {item.is_available ? (
          <button type="button" onClick={() => onAdd(item)}>
            {inCartQty > 0 ? `Add more (${inCartQty})` : "Add to cart"}
          </button>
        ) : (
          <span className="badge">Unavailable</span>
        )}
      </div>
    </div>
  );
}
