import React, { useMemo, useState } from "react";
import { NextUIProvider } from "@nextui-org/react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import HomePage from "./pages/HomePage";
import SummaryPage from "./pages/SummaryPage";
import ExperiencePage from "./pages/ExperiencePage";
import ProjectsPage from "./pages/ProjectsPage";

const App = () => {
  const [mode, setMode] = useState("light");
  const toggleTheme = () =>
    setMode((prev) => (prev === "light" ? "dark" : "light"));

  return (
    <NextUIProvider>
      <Router>
        <Routes>
          <Route
            path="/"
            element={
              <LandingPage
                onEnter={() => (window.location.href = "/home")}
                toggleTheme={toggleTheme}
                mode={mode}
              />
            }
          />
          <Route
            path="/home"
            element={<HomePage toggleTheme={toggleTheme} mode={mode} />}
          />
          <Route
            path="/summary"
            element={<SummaryPage toggleTheme={toggleTheme} mode={mode} />}
          />
          <Route
            path="/experience"
            element={<ExperiencePage toggleTheme={toggleTheme} mode={mode} />}
          />
          <Route
            path="/projects"
            element={<ProjectsPage toggleTheme={toggleTheme} mode={mode} />}
          />
        </Routes>
      </Router>
    </NextUIProvider>
  );
};

export default App;
