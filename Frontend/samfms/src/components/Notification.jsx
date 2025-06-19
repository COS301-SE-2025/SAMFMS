import React, { useState, useEffect } from 'react';

const Notification = ({
  message,
  type = 'info',
  isVisible,
  onClose,
  duration = 5000,
  autoClose = true,
}) => {
  const [isAnimating, setIsAnimating] = useState(false);
  useEffect(() => {
    if (isVisible) {
      setIsAnimating(true);

      if (autoClose && duration > 0) {
        const timer = setTimeout(() => {
          setIsAnimating(false);
          setTimeout(() => {
            onClose();
          }, 300); // Wait for animation to complete
        }, duration);

        return () => clearTimeout(timer);
      }
    }
  }, [isVisible, duration, autoClose, onClose]);

  const handleClose = () => {
    setIsAnimating(false);
    setTimeout(() => {
      onClose();
    }, 300); // Wait for animation to complete
  };

  if (!isVisible) return null;

  const getTypeStyles = () => {
    switch (type) {
      case 'success':
        return {
          bg: 'bg-green-500/10 border-green-500/20',
          text: 'text-green-600 dark:text-green-400',
          icon: '✓',
        };
      case 'error':
        return {
          bg: 'bg-destructive/10 border-destructive/20',
          text: 'text-destructive',
          icon: '✗',
        };
      case 'warning':
        return {
          bg: 'bg-yellow-500/10 border-yellow-500/20',
          text: 'text-yellow-600 dark:text-yellow-400',
          icon: '⚠',
        };
      case 'info':
      default:
        return {
          bg: 'bg-blue-500/10 border-blue-500/20',
          text: 'text-blue-600 dark:text-blue-400',
          icon: 'ℹ',
        };
    }
  };

  const { bg, text, icon } = getTypeStyles();

  return (
    <div className="fixed bottom-4 left-4 z-50 pointer-events-none">
      <div
        className={`
          ${bg} ${text} 
          p-4 rounded-lg border shadow-lg backdrop-blur-sm
          flex items-center space-x-3 min-w-[300px] max-w-[400px]
          pointer-events-auto
          transition-all duration-300 ease-in-out
          ${
            isAnimating
              ? 'transform translate-y-0 opacity-100'
              : 'transform translate-y-full opacity-0'
          }
        `}
      >
        {/* Icon */}
        <div
          className={`
          flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center
          text-sm font-semibold
          ${type === 'success' ? 'bg-green-500/20' : ''}
          ${type === 'error' ? 'bg-destructive/20' : ''}
          ${type === 'warning' ? 'bg-yellow-500/20' : ''}
          ${type === 'info' ? 'bg-blue-500/20' : ''}
        `}
        >
          {icon}
        </div>

        {/* Message */}
        <div className="flex-1 text-sm font-medium">{message}</div>

        {/* Close button */}
        <button
          onClick={handleClose}
          className={`
            flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center
            hover:bg-current/20 transition-colors duration-200
            text-xs font-bold
          `}
          aria-label="Close notification"
        >
          ×
        </button>
      </div>
    </div>
  );
};

export default Notification;
