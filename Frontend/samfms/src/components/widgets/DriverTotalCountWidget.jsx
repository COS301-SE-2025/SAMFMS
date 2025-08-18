import React, {useState, useEffect} from 'react';
import {BaseWidget} from '../dashboard/BaseWidget';
import {getNumberOfDrivers} from '../../backend/api/drivers';
import {registerWidget, WIDGET_TYPES, WIDGET_CATEGORIES} from '../../utils/widgetRegistry';
import {User} from 'lucide-react';

const DriverTotalCountWidget = ({id, config = {}}) => {
    const [driverCount, setDriverCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchDriverCount = async () => {
            try {
                setLoading(true);
                setError(null);
                const count = await getNumberOfDrivers();
                setDriverCount(typeof count === 'number' ? count : 0);
            } catch (err) {
                console.error('Failed to fetch driver count:', err);
                setError('Failed to load driver data');
            } finally {
                setLoading(false);
            }
        };

        fetchDriverCount();

        const refreshInterval = (config.refreshInterval || 60) * 1000;
        const interval = setInterval(fetchDriverCount, refreshInterval);
        return () => clearInterval(interval);
    }, [config.refreshInterval]);

    return (
        <BaseWidget
            id={id}
            title={config.title || 'Total Drivers'}
            loading={loading}
            error={error}
            className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900"
        >
            <div className="flex items-center justify-between h-full">
                <div className="flex-1">
                    <div className="text-3xl font-bold text-green-800 dark:text-green-200 mb-1">
                        {driverCount}
                    </div>
                    <div className="text-sm text-green-600 dark:text-green-400">
                        {driverCount === 1 ? 'Driver' : 'Drivers'} in Fleet
                    </div>
                </div>
                <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-green-200 dark:bg-green-800 rounded-full flex items-center justify-center">
                        <User className="h-6 w-6 text-green-600 dark:text-green-300" />
                    </div>
                </div>
            </div>
        </BaseWidget>
    );
};

registerWidget(WIDGET_TYPES.DRIVER_TOTAL_COUNT, DriverTotalCountWidget, {
    title: 'Total Driver Count',
    description: 'Total count of drivers in the fleet',
    category: WIDGET_CATEGORIES.DRIVERS,
    icon: User,
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
    defaultSize: {w: 3, h: 2},
    minSize: {w: 2, h: 1},
    maxSize: {w: 4, h: 3},
});

export default DriverTotalCountWidget;
