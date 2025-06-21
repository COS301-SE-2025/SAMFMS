import { getToken, getCurrentUser } from '../backend/api/auth';

class SessionMonitor {
  constructor() {
    this.isActive = false;
    this.activityTimer = null;
    this.sessionData = {
      startTime: null,
      lastActivity: null,
      pageViews: 0,
      actions: 0,
      warnings: [],
    };
    this.warningThresholds = {
      sessionDuration: 4 * 60 * 60 * 1000, // 4 hours
      inactivityPeriod: 30 * 60 * 1000, // 30 minutes
      suspiciousActivity: 500, // actions per 5 minutes (increased from 100)
    };
    this.lastActivityWarning = 0; // Track when we last warned about high activity
  }

  /**
   * Start session monitoring
   */
  startMonitoring() {
    if (this.isActive) {
      return;
    }

    this.isActive = true;
    this.sessionData.startTime = Date.now();
    this.sessionData.lastActivity = Date.now();

    // Track user activity
    this.addActivityListeners();

    // Start periodic checks
    this.startPeriodicChecks();

    console.log('Session monitoring started');
  }

  /**
   * Stop session monitoring
   */
  stopMonitoring() {
    if (!this.isActive) {
      return;
    }

    this.isActive = false;
    this.removeActivityListeners();

    if (this.activityTimer) {
      clearInterval(this.activityTimer);
      this.activityTimer = null;
    }

    // Send final session data
    this.sendSessionData();

    console.log('Session monitoring stopped');
  }

  /**
   * Add event listeners for user activity
   */
  addActivityListeners() {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

    events.forEach(event => {
      document.addEventListener(event, this.handleActivity, true);
    });

    // Track page visibility changes
    document.addEventListener('visibilitychange', this.handleVisibilityChange);

    // Track navigation
    window.addEventListener('beforeunload', this.handleBeforeUnload);
  }

  /**
   * Remove event listeners
   */
  removeActivityListeners() {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

    events.forEach(event => {
      document.removeEventListener(event, this.handleActivity, true);
    });

    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
  }

  /**
   * Handle user activity
   */
  handleActivity = event => {
    const now = Date.now();
    this.sessionData.lastActivity = now;
    this.sessionData.actions++;

    // Check for suspicious activity
    this.checkSuspiciousActivity();
  };

  /**
   * Handle page visibility changes
   */
  handleVisibilityChange = () => {
    if (document.hidden) {
      console.log('Page became hidden');
    } else {
      console.log('Page became visible');
      this.sessionData.lastActivity = Date.now();
    }
  };

  /**
   * Handle before page unload
   */
  handleBeforeUnload = () => {
    this.sendSessionData();
  };

  /**
   * Start periodic session checks
   */
  startPeriodicChecks() {
    this.activityTimer = setInterval(() => {
      this.performSessionChecks();
    }, 60000); // Check every minute
  }

  /**
   * Perform periodic session health checks
   */
  performSessionChecks() {
    const now = Date.now();
    const sessionDuration = now - this.sessionData.startTime;
    const inactivityPeriod = now - this.sessionData.lastActivity;

    // Check session duration
    if (sessionDuration > this.warningThresholds.sessionDuration) {
      this.addWarning(
        'long_session',
        `Session has been active for ${Math.round(sessionDuration / 3600000)} hours`
      );
    }

    // Check inactivity
    if (inactivityPeriod > this.warningThresholds.inactivityPeriod) {
      this.addWarning(
        'inactivity',
        `User inactive for ${Math.round(inactivityPeriod / 60000)} minutes`
      );
    }

    // Check token validity
    this.checkTokenHealth();

    // Send periodic session data
    if (sessionDuration % (5 * 60 * 1000) === 0) {
      // Every 5 minutes
      this.sendSessionData();
    }
  }
  /**
   * Check for suspicious activity patterns
   */
  checkSuspiciousActivity() {
    const now = Date.now();

    // Only warn about high activity every 5 minutes to avoid spam
    const timeSinceLastWarning = now - this.lastActivityWarning;
    const fiveMinutes = 5 * 60 * 1000;

    if (
      this.sessionData.actions > this.warningThresholds.suspiciousActivity &&
      timeSinceLastWarning > fiveMinutes
    ) {
      this.addWarning('high_activity', `${this.sessionData.actions} actions in current session`);
      this.lastActivityWarning = now;
    }
  }

  /**
   * Check token health and expiration
   */
  checkTokenHealth() {
    const token = getToken();
    if (!token) {
      this.addWarning('no_token', 'No authentication token found');
      return;
    }

    try {
      // Decode token to check expiry
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiryTime = payload.exp * 1000;
      const currentTime = Date.now();
      const timeUntilExpiry = expiryTime - currentTime;

      if (timeUntilExpiry < 60000) {
        // Less than 1 minute
        this.addWarning(
          'token_expiring',
          `Token expires in ${Math.round(timeUntilExpiry / 1000)} seconds`
        );
      }
    } catch (error) {
      this.addWarning('token_invalid', 'Failed to decode authentication token');
    }
  }
  /**
   * Add a warning to the session data
   */
  addWarning(type, message) {
    const warning = {
      type,
      message,
      timestamp: Date.now(),
    };

    this.sessionData.warnings.push(warning);

    // Only log high activity warnings in development mode to reduce console spam
    if (type === 'high_activity' && process.env.NODE_ENV === 'production') {
      // Don't log high activity warnings in production
      return;
    }

    console.warn(`Session warning [${type}]:`, message);

    // Limit warnings array size
    if (this.sessionData.warnings.length > 50) {
      this.sessionData.warnings = this.sessionData.warnings.slice(-25);
    }
  }

  /**
   * Get current session statistics
   */
  getSessionStats() {
    const now = Date.now();
    return {
      sessionDuration: now - this.sessionData.startTime,
      lastActivity: this.sessionData.lastActivity,
      timeSinceLastActivity: now - this.sessionData.lastActivity,
      pageViews: this.sessionData.pageViews,
      actions: this.sessionData.actions,
      warnings: this.sessionData.warnings.length,
      isActive: this.isActive,
    };
  }

  /**
   * Send session data to analytics endpoint
   */
  async sendSessionData() {
    if (!this.isActive) {
      return;
    }

    try {
      const user = getCurrentUser();
      const sessionStats = this.getSessionStats();

      const analyticsData = {
        userId: user?.id,
        sessionId: this.generateSessionId(),
        ...sessionStats,
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: Date.now(),
      };

      // In a real app, you'd send this to your analytics service
      console.log('Session analytics data:', analyticsData);

      // You could send to an analytics endpoint here
      // await fetch('/api/analytics/session', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(analyticsData)
      // });
    } catch (error) {
      console.error('Failed to send session data:', error);
    }
  }

  /**
   * Generate a session ID
   */
  generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Track page view
   */
  trackPageView(page) {
    this.sessionData.pageViews++;
    this.sessionData.lastActivity = Date.now();
    console.log(`Page view tracked: ${page}`);
  }

  /**
   * Track custom action
   */
  trackAction(action, details = {}) {
    this.sessionData.actions++;
    this.sessionData.lastActivity = Date.now();

    console.log(`Action tracked: ${action}`, details);

    // You could send specific actions to analytics
    // this.sendActionData(action, details);
  }
}

// Singleton instance
const sessionMonitor = new SessionMonitor();

export default sessionMonitor;

// Utility functions
export const startSessionMonitoring = () => sessionMonitor.startMonitoring();
export const stopSessionMonitoring = () => sessionMonitor.stopMonitoring();
export const getSessionStats = () => sessionMonitor.getSessionStats();
export const trackPageView = page => sessionMonitor.trackPageView(page);
export const trackAction = (action, details) => sessionMonitor.trackAction(action, details);
