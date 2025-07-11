import React from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Box,
} from "@mui/material";
import LightModeIcon from "@mui/icons-material/LightMode";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import { useNavigate, useLocation } from "react-router-dom";

const navItems = [
  { label: "首页", path: "/home" },
  { label: "个人总结", path: "/summary" },
  { label: "工作经历", path: "/experience" },
  { label: "项目案例", path: "/projects" },
];

const NavigationBar = ({ toggleTheme, mode }) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <AppBar position="static" color="default" elevation={1} sx={{ mb: 2 }}>
      <Toolbar sx={{ justifyContent: "space-between" }}>
        <Typography
          variant="h6"
          fontWeight={700}
          sx={{ cursor: "pointer", letterSpacing: 2 }}
          onClick={() => navigate("/home")}
        >
          Shang's Website
        </Typography>
        <Box>
          {navItems.map((item) => (
            <Button
              key={item.path}
              color={location.pathname === item.path ? "primary" : "inherit"}
              onClick={() => navigate(item.path)}
              sx={{ fontWeight: 600, mx: 1 }}
            >
              {item.label}
            </Button>
          ))}
        </Box>
        <IconButton onClick={toggleTheme} color="primary" aria-label="切换主题">
          {mode === "light" ? <DarkModeIcon /> : <LightModeIcon />}
        </IconButton>
      </Toolbar>
    </AppBar>
  );
};

export default NavigationBar;
