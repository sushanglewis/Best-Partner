import React, { useState, useEffect } from "react";
import { Box, Typography, Button, IconButton } from "@mui/material";
import LightModeIcon from "@mui/icons-material/LightMode";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import { motion, AnimatePresence } from "framer-motion";
import HeroAnimation from "../components/HeroAnimation";
import SocialIcons from "../components/SocialIcons";

const carouselItems = [
  {
    title: "Hi，欢迎来到我的Agent WebSite",
    subtitle: null
  },
  {
    title: "加入组织",
    subtitle: "招募更多的独立开发者，实现非凡有趣的应用系统，共同进步，共同成功"
  },
  {
    title: "what i want",
    subtitle: "用AI创造艺术，让世界变得更加有趣"
  },
  {
    title: "呼吁",
    subtitle: "让我们一起做点真正有趣的事情"
  }
];

const TextCarousel = ({ mode }) => {
  // 状态管理：控制当前显示的文本索引
  const [index, setIndex] = useState(0);

  // 定时器效果：每4秒切换一次文本
  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % carouselItems.length);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  return (
    <Box sx={{ 
      height: 160, 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center', 
      position: 'relative' 
    }}>
      {/* AnimatePresence 处理进出场动画 */}
      <AnimatePresence mode="wait">
        <motion.div
          key={index}  // key变化触发动画
          initial={{ opacity: 0, y: 20 }}  // 初始状态
          animate={{ opacity: 1, y: 0 }}   // 动画目标状态
          exit={{ opacity: 0, y: -20 }}    // 退出状态
          transition={{ duration: 0.5 }}    // 动画持续时间
          style={{ 
            position: 'absolute',
            width: '100%',
            textAlign: 'center'
          }}
        >
          {/* 标题文本 */}
          <Typography
            variant="h2"
            fontWeight={700}
            color="primary"
            sx={{ mb: 2, textAlign: "center", letterSpacing: 2 }}
          >
            {carouselItems[index].title}
          </Typography>
          {/* 副标题文本（如果存在） */}
          {carouselItems[index].subtitle && (
            <Typography
              variant="h5"
              sx={{
                mb: 4,
                color: mode === "light" ? "#333" : "#EEE",
                textAlign: "center",
              }}
            >
              {carouselItems[index].subtitle}
            </Typography>
          )}
        </motion.div>
      </AnimatePresence>
    </Box>
  );
};

const LandingPage = ({ onEnter, toggleTheme, mode }) => {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background:
          mode === "light"
            ? "linear-gradient(135deg, #F3EFFF 0%, #E3F2FD 100%)"
            : "linear-gradient(135deg, #232136 0%, #1C1B1F 100%)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* 动画/视觉区 */}
      <Box
        sx={{ mb: 4, width: "100%", display: "flex", justifyContent: "center" }}
      >
        <HeroAnimation />
      </Box>
      
      {/* 文字轮播区域 */}
      <TextCarousel mode={mode} />

      <Button
        variant="contained"
        size="large"
        sx={{
          borderRadius: 8,
          px: 6,
          py: 1.5,
          fontWeight: 600,
          fontSize: 20,
          boxShadow: 3,
          mb: 4,
        }}
        onClick={onEnter}
      >
        立即了解
      </Button>
      <IconButton
        onClick={toggleTheme}
        color="primary"
        sx={{ position: "absolute", top: 24, right: 24 }}
        aria-label="切换主题"
      >
        {mode === "light" ? <DarkModeIcon /> : <LightModeIcon />}
      </IconButton>
      {/* 底部社交图标 */}
      <Box
        sx={{
          position: "absolute",
          bottom: 32,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
        }}
      >
        <SocialIcons />
      </Box>
    </Box>
  );
};

export default LandingPage;
