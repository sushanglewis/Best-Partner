import React from "react";
import {
  Box,
  Typography,
  Container,
  Grid,
  Card,
  CardContent,
} from "@mui/material";
import NavigationBar from "../components/NavigationBar";
import FooterBar from "../components/FooterBar";
import { experiences } from "../data/config";

const ExperiencePage = ({ toggleTheme, mode }) => {
  return (
    <Box minHeight="100vh" display="flex" flexDirection="column">
      <NavigationBar toggleTheme={toggleTheme} mode={mode} />
      <Container maxWidth="md" sx={{ flex: 1, py: 6 }}>
        <Typography variant="h5" fontWeight={600} textAlign="center" mb={4}>
          工作经历
        </Typography>
        <Grid container spacing={3}>
          {experiences.map((exp, idx) => (
            <Grid item xs={12} key={idx}>
              <Card sx={{ borderRadius: 4, boxShadow: 2 }}>
                <CardContent>
                  <Typography variant="h6" fontWeight={700}>
                    {exp.company}
                  </Typography>
                  <Typography variant="subtitle2" color="text.secondary" mb={1}>
                    {exp.time} | {exp.role}
                  </Typography>
                  <Typography variant="body1" mb={1}>
                    <b>工作内容：</b>
                    {exp.content}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    <b>工作成果：</b>
                    {exp.result}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
      <FooterBar />
    </Box>
  );
};

export default ExperiencePage;
