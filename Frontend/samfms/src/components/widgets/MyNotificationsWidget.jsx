import React, {useState, useEffect} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {getUserNotifications} from '../../backend/api/notifications';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {Bell} from 'lucide-react';

const MyNotificationsWidget = ({id, config = {}}) => {
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchNotifications = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await getUserNotifications();
                setNotifications(Array.isArray(response) ? response : []);
            } catch (err) {
                console.error('Failed to fetch notifications:', err);
                setError('Failed to load notifications');
            } finally {
                setLoading(false);
            }
        };

        fetchNotifications();

        const refreshInterval = (config.refreshInterval || 60) * 1000;
        const interval = setInterval(fetchNotifications, refreshInterval);
        return () => clearInterval(interval);
    }, [config.refreshInterval]);

    return (
        <BaseWidget
            id={id}
            title={config.title || 'My Notifications'}
            loading={loading}
            error={error}
            className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-950 dark:to-yellow-900"
        >
            <div className="flex items-center justify-between h-full">
                <div className="flex-1 overflow-y-auto max-h-40 pr-2">
                    {notifications.length === 0 ? (
                        <div className="text-sm text-yellow-600 dark:text-yellow-400">No notifications</div>
                    ) : (
                        <ul className="space-y-2">
                            {notifications.slice(0, 5).map((notif, idx) => (
                                <li key={notif.id || idx} className="bg-yellow-100 dark:bg-yellow-900 rounded px-3 py-2 text-yellow-900 dark:text-yellow-100 text-xs">
                                    {notif.message || notif.text || 'Notification'}
                                    {notif.timestamp && (
                                        <span className="block text-[10px] text-yellow-700 dark:text-yellow-300 mt-1">{new Date(notif.timestamp).toLocaleString()}</span>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
                <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-yellow-200 dark:bg-yellow-800 rounded-full flex items-center justify-center">
                        <Bell className="h-6 w-6 text-yellow-600 dark:text-yellow-300" />
                    </div>
                </div>
            </div>
        </BaseWidget>
    );
};

registerWidget(WIDGET_TYPES.MY_NOTIFICATIONS, MyNotificationsWidget, {
    title: 'My Notifications',
    description: 'Shows your latest notifications',
    category: WIDGET_CATEGORIES.NOTIFICATIONS,
    icon: Bell,
    defaultConfig: {
        refreshInterval: 60,
    },
    configSchema: {
        refreshInterval: {
            type: 'number',
            label: 'Refresh Interval (seconds)',
            min: 30,
            max: 3600,
            default: 60,
        },
    },
    defaultSize: {w: 3, h: 6},
    minSize: {w: 3, h: 3},
    maxSize: {w: 8, h: 8},
});

export default MyNotificationsWidget;
