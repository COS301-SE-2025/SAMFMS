import React from 'react';

const FadeIn = ({
  children,
  delay = 0,
  duration = 0.6,
  className = '',
  direction = 'up', // 'up', 'down', 'left', 'right', 'none'
}) => {
  const getTransform = () => {
    switch (direction) {
      case 'up':
        return 'translateY(20px)';
      case 'down':
        return 'translateY(-20px)';
      case 'left':
        return 'translateX(20px)';
      case 'right':
        return 'translateX(-20px)';
      default:
        return 'none';
    }
  };

  const animationStyle = {
    animation: `fadeIn ${duration}s ease-out ${delay}s both`,
    transformOrigin: 'center',
  };

  const keyframeStyle = `
    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: ${getTransform()};
      }
      to {
        opacity: 1;
        transform: translate(0, 0);
      }
    }
  `;

  return (
    <>
      <style>{keyframeStyle}</style>
      <div style={animationStyle} className={className}>
        {children}
      </div>
    </>
  );
};

export default FadeIn;
