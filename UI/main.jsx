import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import SentimentIQ from "./SentimentIQ";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <SentimentIQ />
  </StrictMode>
);
