import React from "react";
import {
  Box,
  Typography,
  Container,
  Grid,
  Card,
  CardContent,
  Button,
} from "@mui/material";
import NavigationBar from "../components/NavigationBar";
import FooterBar from "../components/FooterBar";
import { summaryCards } from "../data/config";

const SummaryPage = ({ toggleTheme, mode }) => {
  return (
    <Box minHeight="100vh" display="flex" flexDirection="column">
      <NavigationBar toggleTheme={toggleTheme} mode={mode} />
      <Container maxWidth="md" sx={{ flex: 1, py: 6 }}>
        <Typography variant="h5" fontWeight={600} textAlign="center" mb={4}>
          用我的技能、经验与知识，帮助团队达成目标
        </Typography>
        <Grid container spacing={3} mb={4}>
          {summaryCards.map((card, idx) => (
            <Grid item xs={12} sm={6} key={idx}>
              <Card sx={{ borderRadius: 4, boxShadow: 2 }}>
                <CardContent>
                  <Typography variant="h6" fontWeight={700} mb={1}>
                    {card.title}
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    {card.desc}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
        <Box textAlign="center">
          <Button
            variant="contained"
            size="large"
            sx={{ borderRadius: 6, px: 5, py: 1.2, fontWeight: 600 }}
          >
            让我们一起做点事情！
          </Button>
        </Box>
      </Container>
      <FooterBar />
    </Box>
  );
};

export default SummaryPage;
