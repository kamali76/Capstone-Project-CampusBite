import client from "./client";
import { cleanParams } from "../utils/format";

export const getRestaurants = () => client.get("/restaurants");

export const getRestaurant = (id) => client.get(`/restaurants/${id}`);

// Filters map to the backend query params: search, min_price, max_price
export const getMenu = (id, { search = "", minPrice = "", maxPrice = "" } = {}) =>
  client.get(`/restaurants/${id}/menu`, {
    params: cleanParams({ search: search.trim(), min_price: minPrice, max_price: maxPrice }),
  });
