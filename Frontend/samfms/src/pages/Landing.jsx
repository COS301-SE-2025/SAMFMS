import React, {useState, useEffect} from 'react';
import {Button} from '../components/ui/button';
import {useNavigate} from 'react-router-dom';
import {
    checkUserExistence,
    clearUserExistenceCache,
    isAuthenticated
} from '../backend/API.js';
import {
    Car,
    Shield,
    Map,
    BarChart,
    Zap,
    ChevronRight
} from 'lucide-react';

const FeatureCard = ({icon, title, description}) => (
    <div className="bg-card rounded-lg p-6 shadow-md border border-border hover:shadow-lg transition-all duration-300 hover:-translate-y-1 pt-10 pb-10">
        <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-full bg-primary/10 text-primary">
                {icon}
            </div>
            <h3 className="text-xl font-semibold">{title}</h3>
        </div>
        <p className="text-muted-foreground">{description}</p>
    </div>
);

const Landing = () => {
    const navigate = useNavigate();
    const [checkingStatus, setCheckingStatus] = useState(true);
    const [hasExistingUsers, setHasExistingUsers] = useState(null);

    useEffect(() => {
        // If user is already authenticated, redirect to dashboard
        if (isAuthenticated()) {
            navigate('/dashboard');
            return;
        }

        // Clean up any cached user existence data
        clearUserExistenceCache();

        // Add a safety timeout to prevent infinite loading
        const timeoutId = setTimeout(() => {
            setCheckingStatus(false);
        }, 3000);

        const checkSystemStatus = async () => {
            try {
                // Check if users exist in the system
                const usersExist = await checkUserExistence(true);
                setHasExistingUsers(usersExist);
            } catch (error) {
                console.error('Error checking system status:', error);
                // Default to assuming users exist if there's an error
                setHasExistingUsers(true);
            } finally {
                setCheckingStatus(false);
            }
        };

        checkSystemStatus();
        return () => clearTimeout(timeoutId);
    }, [navigate]);

    const handleGetStarted = () => {
        // Navigate to login if users exist, otherwise signup
        if (hasExistingUsers) {
            navigate('/login');
        } else {
            navigate('/signup');
        }
    };

    // Display loading state while checking for users
    if (checkingStatus) {
        return (
            <div className="min-h-screen flex justify-center items-center bg-background">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-primary">Initializing system...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background">
            {/* Hero Section */}
            <div className="relative overflow-hidden">
                <div
                    className="absolute inset-0 z-0 opacity-10"
                    style={{
                        backgroundImage: 'url("/logo/logo_icon_dark.svg")',
                        backgroundSize: '200px',
                        backgroundRepeat: 'repeat',
                        filter: 'blur(1px)',
                    }}
                />
                <div className="container mx-auto px-4 py-24 lg:py-32 relative z-10">
                    <div className="flex flex-col md:flex-row items-center justify-between">
                        <div className="md:w-1/2 mb-12 md:mb-0">
                            <img
                                src="/logo/logo_horisontal_light.svg"
                                alt="SAMFMS Logo"
                                className="h-16 mb-8 animate-fadeIn transition-all duration-300 dark:hidden"
                            />
                            <img
                                src="/logo/logo_horisontal_dark.svg"
                                alt="SAMFMS Logo"
                                className="h-16 mb-8 animate-fadeIn transition-all duration-300 hidden dark:block"
                            />
                            <h1 className="text-5xl md:text-6xl font-bold mb-6 text-foreground">
                                Smart Fleet Management at Your Fingertips
                            </h1>
                            <p className="text-xl text-muted-foreground mb-8">
                                Streamline your fleet operations, optimize vehicle maintenance, and track your assets with our comprehensive management system.
                            </p>
                            <div>
                                <Button
                                    size="lg"
                                    onClick={handleGetStarted}
                                    className="bg-primary hover:bg-primary/90 text-white px-8 py-6 h-auto text-lg font-medium flex items-center gap-2 transform transition-all duration-300 hover:scale-105"
                                >
                                    {hasExistingUsers ? 'Login to Account' : 'Create First Account'}
                                    <ChevronRight size={20} />
                                </Button>
                            </div>
                        </div>
                        <div className="md:w-1/2 flex justify-center">
                            <div className="relative w-full max-w-md">
                                <div className="absolute -top-6 -left-6 w-full h-full rounded-xl bg-primary/20 transform -rotate-3"></div>
                                <div className="absolute -bottom-6 -right-6 w-full h-full rounded-xl bg-primary/30 transform rotate-3"></div>
                                <div className="relative bg-card rounded-xl overflow-hidden shadow-2xl border border-border transform hover:rotate-0 transition-all duration-500 hover:scale-105">
                                    <img
                                        src="/logo/logo_icon_light.svg"
                                        alt="SAMFMS Dashboard Preview"
                                        className="w-full p-12 dark:hidden"
                                    />
                                    <img
                                        src="/logo/logo_icon_dark.svg"
                                        alt="SAMFMS Dashboard Preview"
                                        className="w-full p-12 hidden dark:block"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Features Section */}
            <div className="bg-accent/10 py-16">
                <div className="container mx-auto px-4">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-bold mb-4">Powerful Fleet Management Features</h2>
                        <p className="text-muted-foreground max-w-2xl mx-auto">
                            Everything you need to manage your fleet efficiently and effectively in one integrated platform.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        <FeatureCard
                            icon={<Car size={24} />}
                            title="Vehicle Management"
                            description="Comprehensive vehicle inventory, maintenance history, and performance analytics all in one place."
                        />
                        <FeatureCard
                            icon={<Map size={24} />}
                            title="Real-time Tracking"
                            description="Monitor your fleet's location in real-time with advanced GPS tracking and route optimization."
                        />
                        <FeatureCard
                            icon={<Shield size={24} />}
                            title="Enhanced Security"
                            description="Role-based access control and comprehensive audit trails to keep your data secure."
                        />
                        <FeatureCard
                            icon={<BarChart size={24} />}
                            title="Advanced Analytics"
                            description="Data-driven insights to optimize routes, reduce costs, and improve fleet performance."
                        />
                        <FeatureCard
                            icon={<Zap size={24} />}
                            title="Maintenance Alerts"
                            description="Proactive maintenance scheduling and alerts to prevent breakdowns and extend vehicle life."
                        />
                        <FeatureCard
                            icon={<ChevronRight size={24} />}
                            title="And Much More"
                            description="Discover all the features by logging in or signing up to experience the full platform."
                        />
                    </div>
                </div>
            </div>

            {/* CTA Section */}
            <div className="container mx-auto px-4 py-20">
                <div className="bg-card rounded-2xl p-8 md:p-12 border border-border shadow-lg">
                    <div className="flex flex-col md:flex-row items-center justify-between">
                        <div className="md:w-2/3 mb-8 md:mb-0">
                            <h2 className="text-3xl font-bold mb-4">Ready to optimize your fleet operations?</h2>
                            <p className="text-muted-foreground text-lg">
                                Join thousands of fleet managers who have transformed their operations with SAMFMS.
                            </p>
                        </div>
                        <Button
                            size="lg"
                            onClick={handleGetStarted}
                            className="bg-primary hover:bg-primary/90 px-8 h-14 text-lg font-medium"
                        >
                            {hasExistingUsers ? 'Login Now' : 'Get Started'}
                        </Button>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer className="bg-card border-t border-border">
                <div className="container mx-auto px-4 py-8">
                    <div className="flex flex-col md:flex-row justify-between items-center">
                        <div className="mb-4 md:mb-0">
                            <img
                                src="/logo/logo_horisontal_light.svg"
                                alt="SAMFMS Logo"
                                className="h-8 dark:hidden"
                            />
                            <img
                                src="/logo/logo_horisontal_dark.svg"
                                alt="SAMFMS Logo"
                                className="h-8 hidden dark:block"
                            />
                        </div>
                        <div className="text-muted-foreground text-sm">
                            &copy; {new Date().getFullYear()} SAMFMS. All rights reserved.
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default Landing;