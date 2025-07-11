import React from "react";
import {
  Box,
  Typography,
  Container,
  Grid,
  Card,
  CardContent,
  Chip,
  Stack,
} from "@mui/material";
import NavigationBar from "../components/NavigationBar";
import FooterBar from "../components/FooterBar";
import { projects } from "../data/config";

const ProjectsPage = ({ toggleTheme, mode }) => {
  return (
    <Box minHeight="100vh" display="flex" flexDirection="column">
      <NavigationBar toggleTheme={toggleTheme} mode={mode} />
      <Container maxWidth="md" sx={{ flex: 1, py: 6 }}>
        <Typography variant="h5" fontWeight={600} textAlign="center" mb={4}>
          项目案例
        </Typography>
        <Grid container spacing={3}>
          {projects.map((proj, idx) => (
            <Grid item xs={12} key={idx}>
              <Card sx={{ borderRadius: 4, boxShadow: 2 }}>
                <CardContent>
                  <Typography variant="h6" fontWeight={700}>
                    {proj.name}
                  </Typography>
                  <Typography variant="subtitle2" color="text.secondary" mb={1}>
                    {proj.time}
                  </Typography>
                  <Typography variant="body1" mb={1}>
                    {proj.desc}
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {proj.tags &&
                      proj.tags.map((tag, i) => (
                        <Chip
                          key={i}
                          label={tag}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      ))}
                  </Stack>
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

export default ProjectsPage;
