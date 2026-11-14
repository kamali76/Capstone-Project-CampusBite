import { useCallback, useEffect, useMemo, useReducer } from "react";
import { CartContext } from "./CartContext";
import { CART_KEY_PREFIX } from "../utils/constants";

const MAX_QTY = 20;
const emptyCart = { restaurant: null, items: [] };

// A cart belongs to ONE restaurant: adding a dish from another restaurant starts a new cart.
function cartReducer(state, action) {
  switch (action.type) {
    case "ADD": {
      const { restaurant, item } = action;
      const base = state.restaurant?.id === restaurant.id ? state : { restaurant, items: [] };
      const existing = base.items.find((i) => i.id === item.id);
      const items = existing
        ? base.items.map((i) =>
            i.id === item.id ? { ...i, quantity: Math.min(i.quantity + 1, MAX_QTY) } : i
          )
        : [...base.items, { id: item.id, name: item.name, price: item.price, quantity: 1 }];
      return { restaurant: base.restaurant, items };
    }
    case "SET_QUANTITY": {
      const items = state.items
        .map((i) =>
          i.id === action.id ? { ...i, quantity: Math.min(action.quantity, MAX_QTY) } : i
        )
        .filter((i) => i.quantity > 0);
      return items.length ? { ...state, items } : emptyCart;
    }
    case "REMOVE": {
      const items = state.items.filter((i) => i.id !== action.id);
      return items.length ? { ...state, items } : emptyCart;
    }
    case "CLEAR":
      return emptyCart;
    default:
      return state;
  }
}

const loadCart = (storageKey) => {
  try {
    const raw = localStorage.getItem(storageKey);
    return raw ? JSON.parse(raw) : emptyCart;
  } catch {
    return emptyCart;
  }
};

// Mounted with key={userId} (see App.jsx) so every user gets their own saved cart.
export default function CartProvider({ userId, children }) {
  const storageKey = `${CART_KEY_PREFIX}${userId ?? "guest"}`;
  const [cart, dispatch] = useReducer(cartReducer, storageKey, loadCart);

  // Persist the cart so it survives page refreshes
  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify(cart));
  }, [cart, storageKey]);

  const addItem = useCallback((restaurant, item) => dispatch({ type: "ADD", restaurant, item }), []);
  const setQuantity = useCallback((id, quantity) => dispatch({ type: "SET_QUANTITY", id, quantity }), []);
  const removeItem = useCallback((id) => dispatch({ type: "REMOVE", id }), []);
  const clearCart = useCallback(() => dispatch({ type: "CLEAR" }), []);

  const value = useMemo(() => {
    const totalItems = cart.items.reduce((sum, i) => sum + i.quantity, 0);
    const totalPrice = cart.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
    return {
      restaurant: cart.restaurant,
      items: cart.items,
      totalItems,
      totalPrice,
      addItem,
      setQuantity,
      removeItem,
      clearCart,
      maxQuantity: MAX_QTY,
    };
  }, [cart, addItem, setQuantity, removeItem, clearCart]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}
