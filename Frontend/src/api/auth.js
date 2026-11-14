import client from "./client";

export const loginUser = (email, password) => client.post("/auth/login", { email, password });

export const registerUser = (payload) => client.post("/auth/register", payload);

export const fetchMe = () => client.get("/auth/me");
