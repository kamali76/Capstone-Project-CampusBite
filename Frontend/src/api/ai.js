import client from "./client";
import { getTzOffset } from "../utils/format";

// The backend reads the customer's id from the JWT, so we only ever send the question
// (plus our time-zone offset, so "this week" means the user's local week).
export const askOrderInsights = (question) =>
  client.post("/ai/insights", { question, tz_offset: getTzOffset() });
