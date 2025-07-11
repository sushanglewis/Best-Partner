import React from "react";
import { Box, Typography, Container } from "@mui/material";
import NavigationBar from "../components/NavigationBar";
import FooterBar from "../components/FooterBar";

const HomePage = ({ toggleTheme, mode }) => {
  return (
    <Box minHeight="100vh" display="flex" flexDirection="column">
      <NavigationBar toggleTheme={toggleTheme} mode={mode} />
      <Container
        maxWidth="md"
        sx={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Typography variant="h4" fontWeight={600} textAlign="center">
          Hi，我是苏尚，欢迎来到我的个人站，在这里你可以详细了解我的信息，期待你的联系
        </Typography>
      </Container>
      <FooterBar />
    </Box>
  );
};

export default HomePage;
