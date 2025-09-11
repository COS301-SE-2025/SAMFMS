import { Vibration } from 'react-native';

class NotificationService {
  private initialized = false;

  configure() {
    if (this.initialized) return;

    console.log('NotificationService: Configured successfully');
    this.initialized = true;
  }

  // No grace period warnings anymore

  showViolationAlert(violationType: string) {
    try {
      // Use a stronger vibration pattern for violations to make them more noticeable
      try {
        // More intense vibration pattern: 3 long pulses
        Vibration.vibrate([800, 200, 800, 200, 800]);
      } catch (vibrationError) {
        console.warn('Vibration failed:', vibrationError);
      }

      // Make violation logging more noticeable in console
      console.log('==============================');
      console.log(`🚨 VIOLATION ALERT: ${violationType}`);
      console.log('==============================');

      // For now, we'll use console logging and vibration instead of push notifications
      // In a production app, this would show a system notification
    } catch (error) {
      console.error('NotificationService: Error showing violation alert:', error);
    }
  }

  // No more grace period cancellation needed

  cancelAllNotifications() {
    try {
      console.log('All notifications cancelled');
      // Cancel all pending notifications
    } catch (error) {
      console.error('NotificationService: Error cancelling all notifications:', error);
    }
  }

  showOngoingMonitoring() {
    try {
      // Vibrate once briefly to indicate monitoring has started
      Vibration.vibrate(200);

      console.log('Driver behavior monitoring is active in background');

      // In a production app, this would create a persistent notification
      // to keep the app running in the background, especially on Android
      // For now, we're using console logging as a placeholder
    } catch (error) {
      console.error('NotificationService: Error showing ongoing monitoring notification:', error);
    }
  }
}

export default new NotificationService();
