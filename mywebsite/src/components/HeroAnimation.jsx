import React, { useEffect, useRef } from "react";

// 简单 Canvas 粒子/流光动画骨架
const HeroAnimation = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let animationId;
    let t = 0;
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      // 渐变流光圆环
      const gradient = ctx.createLinearGradient(
        0,
        0,
        canvas.width,
        canvas.height,
      );
      gradient.addColorStop(0, "#7F39FB");
      gradient.addColorStop(1, "#6750A4");
      ctx.beginPath();
      ctx.arc(
        canvas.width / 2,
        canvas.height / 2,
        90 + 10 * Math.sin(t / 20),
        0,
        2 * Math.PI,
      );
      ctx.strokeStyle = gradient;
      ctx.lineWidth = 16 + 4 * Math.cos(t / 30);
      ctx.shadowBlur = 32;
      ctx.shadowColor = "#7F39FB";
      ctx.stroke();
      ctx.shadowBlur = 0;
      // 粒子点
      for (let i = 0; i < 24; i++) {
        const angle = (i / 24) * 2 * Math.PI + t / 40;
        const r = 90 + 20 * Math.sin(t / 30 + i);
        const x = canvas.width / 2 + r * Math.cos(angle);
        const y = canvas.height / 2 + r * Math.sin(angle);
        ctx.beginPath();
        ctx.arc(x, y, 4 + 2 * Math.sin(t / 10 + i), 0, 2 * Math.PI);
        ctx.fillStyle = "#D0BCFF";
        ctx.globalAlpha = 0.7;
        ctx.fill();
        ctx.globalAlpha = 1;
      }
      t++;
      animationId = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(animationId);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      width={220}
      height={220}
      style={{ display: "block", margin: "0 auto", borderRadius: "50%" }}
    />
  );
};

export default HeroAnimation;
