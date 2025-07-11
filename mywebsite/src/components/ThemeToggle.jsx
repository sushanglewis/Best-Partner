import React from "react";
import { Button } from "@nextui-org/react";

const ThemeToggle = ({ mode, toggleTheme }) => (
  <Button
    isIconOnly
    variant="light"
    color="primary"
    onClick={toggleTheme}
    aria-label="切换主题"
    className="transition-transform hover:scale-105"
  >
    {mode === "light" ? "🌙" : "☀️"}
  </Button>
);

export default ThemeToggle;
