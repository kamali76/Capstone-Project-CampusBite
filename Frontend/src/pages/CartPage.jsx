import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import useCart from "../hooks/useCart";
import { placeOrder } from "../api/orders";
import ErrorMessage from "../components/ErrorMessage";
import { getErrorMessage } from "../utils/errors";
import { formatPrice } from "../utils/format";

export default function CartPage() {
  const cart = useCart();
  const navigate = useNavigate();
  const [address, setAddress] = useState("");
  const [error, setError] = useState("");
  const [placing, setPlacing] = useState(false);

  const handleCheckout = async (e) => {
    e.preventDefault();
    setError("");
    setPlacing(true);
    try {
      const { data: order } = await placeOrder({
        restaurant_id: cart.restaurant.id,
        delivery_address: address.trim(),
        items: cart.items.map((i) => ({ menu_item_id: i.id, quantity: i.quantity })),
      });
      cart.clearCart();
      navigate("/orders", { state: { placedOrderId: order.id } });
    } catch (err) {
      setError(getErrorMessage(err));
      setPlacing(false);
    }
  };

  if (cart.items.length === 0) {
    return (
      <div>
        <h2>Your cart</h2>
        <p>Your cart is empty.</p>
        <Link to="/restaurants">Browse restaurants</Link>
      </div>
    );
  }

  return (
    <div>
      <h2>Cart &amp; checkout</h2>
      <p className="muted">
        Ordering from <strong>{cart.restaurant.name}</strong>
      </p>

      <div className="card">
        <ul className="cart-list">
          {cart.items.map((item) => (
            <li key={item.id} className="cart-row">
              <div className="cart-row-name">
                <strong>{item.name}</strong>
                <span className="muted">{formatPrice(item.price)} each</span>
              </div>
              <div className="qty-controls">
                <button
                  type="button"
                  className="secondary"
                  aria-label={`Decrease ${item.name}`}
                  onClick={() => cart.setQuantity(item.id, item.quantity - 1)}
                >
                  −
                </button>
                <span>{item.quantity}</span>
                <button
                  type="button"
                  className="secondary"
                  aria-label={`Increase ${item.name}`}
                  disabled={item.quantity >= cart.maxQuantity}
                  onClick={() => cart.setQuantity(item.id, item.quantity + 1)}
                >
                  +
                </button>
              </div>
              <strong className="cart-row-total">{formatPrice(item.price * item.quantity)}</strong>
              <button type="button" className="link-button" onClick={() => cart.removeItem(item.id)}>
                Remove
              </button>
            </li>
          ))}
        </ul>
        <p className="cart-total">
          Total: <strong>{formatPrice(cart.totalPrice)}</strong>
        </p>
      </div>

      <form className="card checkout-form" onSubmit={handleCheckout}>
        <h3>Delivery details</h3>
        <ErrorMessage message={error} />
        <div className="form-group">
          <label htmlFor="address">Delivery address</label>
          <textarea
            id="address"
            rows={3}
            minLength={5}
            maxLength={500}
            required
            placeholder="Hostel / block, room number, landmark"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
          />
        </div>
        <p className="muted">
          💳 This is a dummy payment: no real money is charged. The order is marked as paid
          (mock_paid) when you place it.
        </p>
        <div className="checkout-actions">
          <button type="submit" disabled={placing}>
            {placing ? "Placing order..." : `Place order · ${formatPrice(cart.totalPrice)}`}
          </button>
          <button type="button" className="secondary" disabled={placing} onClick={cart.clearCart}>
            Clear cart
          </button>
        </div>
      </form>
    </div>
  );
}
