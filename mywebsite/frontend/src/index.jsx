import React from "react";
import { createRoot } from "react-dom/client";
import { NextUIProvider } from "@nextui-org/react";
import App from "./App.jsx";
import "./styles/global.css";

const container = document.getElementById("root");
const root = createRoot(container);
root.render(
  <React.StrictMode>
    <NextUIProvider>
      <App />
    </NextUIProvider>
  </React.StrictMode>,
);
