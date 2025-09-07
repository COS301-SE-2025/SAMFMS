"use client";
import { cn } from "../../lib/utils";
import { motion } from "framer-motion";

export const Spotlight = ({
  className,
  gradientFirst = "radial-gradient(68.54% 68.72% at 55.02% 31.46%, hsla(210, 100%, 85%, .08) 0, hsla(210, 100%, 55%, .02) 50%, hsla(210, 100%, 45%, 0) 80%)",
  gradientSecond = "radial-gradient(50% 50% at 50% 50%, hsla(210, 100%, 85%, .06) 0, hsla(210, 100%, 55%, .02) 80%, transparent 100%)",
  gradientThird = "radial-gradient(50% 50% at 50% 50%, hsla(210, 100%, 85%, .04) 0, hsla(210, 100%, 45%, .02) 80%, transparent 100%)",
  translateY = -350,
  width = 560,
  height = 1380,
  smallWidth = 240,
  duration = 7,
  xOffset = 100,
}) => {
  return (
    <div className={cn("pointer-events-none absolute inset-0", className)}>
      <motion.div
        className="pointer-events-none absolute"
        style={{
          background: gradientFirst,
          transform: `translateY(${translateY}px) translateX(${xOffset}px)`,
          width: `${width}px`,
          height: `${height}px`,
          left: '10%',
          top: '0%',
        }}
        animate={{
          x: [0, xOffset, 0],
          y: [0, -50, 0],
        }}
        transition={{
          duration: duration,
          repeat: Infinity,
          repeatType: "reverse",
          ease: "easeInOut",
        }}
      />
      <motion.div
        className="pointer-events-none absolute"
        style={{
          background: gradientSecond,
          transform: `translateY(${translateY + 100}px) translateX(${-xOffset}px)`,
          width: `${width * 0.8}px`,
          height: `${height}px`,
          right: '10%',
          top: '10%',
        }}
        animate={{
          x: [0, -xOffset * 0.8, 0],
          y: [0, 30, 0],
        }}
        transition={{
          duration: duration * 1.2,
          repeat: Infinity,
          repeatType: "reverse",
          ease: "easeInOut",
          delay: 0.5,
        }}
      />
      <motion.div
        className="pointer-events-none absolute"
        style={{
          background: gradientThird,
          width: `${width * 0.6}px`,
          height: `${height * 0.8}px`,
          left: '50%',
          top: '20%',
          transform: `translateX(-50%) translateY(${translateY + 200}px)`,
        }}
        animate={{
          x: [0, xOffset * 0.6, 0],
          y: [0, -20, 0],
        }}
        transition={{
          duration: duration * 0.8,
          repeat: Infinity,
          repeatType: "reverse",
          ease: "easeInOut",
          delay: 1,
        }}
      />
    </div>
  );
};
