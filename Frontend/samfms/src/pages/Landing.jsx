import React, {useState, useEffect} from 'react';
import {Button} from '../components/ui/button';
import Modal from '../components/ui/Modal';
import LoginForm from '../components/auth/LoginForm';
import {TypewriterEffectSmooth} from '../components/ui/typewriter-effect';
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
    ChevronRight,
    Github
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
    const [showLoginModal, setShowLoginModal] = useState(false);

    const [currentHeadingIndex] = useState(0);

    const headings = [
        [
            {text: "Smart"},
            {text: "Fleet", className: "text-blue-500 dark:text-blue-400"},
            {text: "Management", className: "text-blue-500 dark:text-blue-400"},
            {text: "at your"},
            {text: "fingertips"}
        ],
        [
            {text: "Optimize"},
            {text: "Vehicle", className: "text-green-500 dark:text-green-400"},
            {text: "Utilization", className: "text-green-500 dark:text-green-400"},
        ],
        [
            {text: "Track"},
            {text: "Assets", className: "text-purple-500 dark:text-purple-400"},
            {text: "in", className: "text-purple-500 dark:text-purple-400"},
            {text: "real-time"}
        ],
        [
            {text: "Streamline"},
            {text: "Operations", className: "text-orange-500 dark:text-orange-400"},
            {text: "effortlessly", className: "text-orange-500 dark:text-orange-400"}
        ]
    ];

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
        // Show login modal if users exist, otherwise navigate to signup
        if (hasExistingUsers) {
            setShowLoginModal(true);
        } else {
            navigate('/signup');
        }
    };

    const handleLoginSuccess = () => {
        setShowLoginModal(false);
        // Navigation is handled within the LoginForm component
    };

    const handleCloseModal = () => {
        setShowLoginModal(false);
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
        <>
            <div className="bg-background">
                {/* Hero Section - Fixed */}
                <div className="fixed top-0 left-0 w-full h-screen overflow-hidden bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 group z-10">
                {/* Gradient Background */}
                <div className="absolute inset-0 bg-gradient-to-br from-blue-50/20 via-purple-50/10 to-slate-50/20 dark:from-blue-950/20 dark:via-purple-950/10 dark:to-slate-950/20"></div>
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
                            <TypewriterEffectSmooth 
                                words={[
                                    { text: "Smart" },
                                    { text: "Fleet" },
                                    { text: "Management", className: "text-blue-500 dark:text-blue-400" },
                                    { text: "at" },
                                    { text: "Your" },
                                    { text: "Fingertips", className: "text-blue-500 dark:text-blue-400" }
                                ]}
                                className="mb-6"
                            />

                            <div className='text-sm text-muted-foreground pl-14 mb-4'><p>by Firewall Five</p></div>
                            <div className="w-full">
                                <TypewriterEffectSmooth
                                    key={currentHeadingIndex} // Force re-render when heading changes
                                    words={headings[currentHeadingIndex]}
                                    className="mb-6"
                                />
                            </div>
                            <p className="text-xl text-muted-foreground mb-8">
                                Streamline your fleet operations, optimize vehicle maintenance, and track your assets with our comprehensive management system.
                            </p>
                            <div className="flex justify-center md:justify-start">
                                <Button
                                    size="lg"
                                    onClick={handleGetStarted}

                                    className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-12 py-4 h-auto text-lg font-semibold flex items-center gap-3 rounded-xl shadow-lg hover:shadow-xl transform transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] focus:ring-4 focus:ring-blue-300 dark:focus:ring-blue-800 border-0 relative overflow-hidden group"
                                >
                                    {hasExistingUsers ? 'Login to Account' : 'Create First Account'}
                                    <ChevronRight size={20} />
                                </Button>


                                <div className="flex gap-3">
                                    <Button
                                        variant="outline"
                                        size="lg"
                                        onClick={() => window.open('https://github.com/COS301-SE-2025/SAMFMS', '_blank')}
                                        className="border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 px-6 py-3 h-auto text-base font-medium flex items-center gap-3 rounded-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
                                    >
                                        <Github size={20} />
                                        GitHub
                                    </Button>

                                    <Button
                                        variant="outline"
                                        size="lg"
                                        onClick={() => window.open('https://github.com/COS301-SE-2025/SAMFMS/blob/main/docs/Demo3/SAMFMS%20User%20Manual.pdf', '_blank')}
                                        className="border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 px-6 py-3 h-auto text-base font-medium flex items-center gap-3 rounded-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
                                    >
                                        <BarChart size={20} />
                                        Guide
                                    </Button>
                                </div>
                            </div>
                        </div>

                        {/* Right side - Feature Cards */}
                        <div className="w-full md:w-1/2 relative flex items-center justify-center min-h-[600px] pt-8">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-lg">
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 transform hover:scale-105 transition-transform duration-300">
                                    <img
                                        src="/images/image.png"
                                        alt="Fleet Management"
                                        className="w-full h-32 object-cover rounded-lg mb-3"
                                    />
                                    <div className="flex items-center gap-2 mb-2">
                                        <Car size={16} className="text-blue-500" />
                                        <h3 className="text-sm font-medium">Vehicle Tracking</h3>
                                    </div>
                                    <p className="text-xs text-gray-600 dark:text-gray-400">Real-time GPS tracking and route optimization.</p>
                                </div>
                                
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 transform hover:scale-105 transition-transform duration-300">
                                    <img
                                        src="/images/image.png"
                                        alt="Security & Safety"
                                        className="w-full h-32 object-cover rounded-lg mb-3"
                                    />
                                    <div className="flex items-center gap-2 mb-2">
                                        <Shield size={16} className="text-green-500" />
                                        <h3 className="text-sm font-medium">Security & Safety</h3>
                                    </div>
                                    <p className="text-xs text-gray-600 dark:text-gray-400">Advanced security features and driver safety monitoring.</p>
                                </div>
                                
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 transform hover:scale-105 transition-transform duration-300">
                                    <img
                                        src="/images/image.png"
                                        alt="Analytics & Reports"
                                        className="w-full h-32 object-cover rounded-lg mb-3"
                                    />
                                    <div className="flex items-center gap-2 mb-2">
                                        <BarChart size={16} className="text-purple-500" />
                                        <h3 className="text-sm font-medium">Analytics & Reports</h3>
                                    </div>
                                    <p className="text-xs text-gray-600 dark:text-gray-400">Comprehensive analytics and reporting for data-driven decisions.</p>
                                </div>
                                
                                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 transform hover:scale-105 transition-transform duration-300">
                                    <img
                                        src="/images/image.png"
                                        alt="Smart Automation"
                                        className="w-full h-32 object-cover rounded-lg mb-3"
                                    />
                                    <div className="flex items-center gap-2 mb-2">
                                        <Zap size={16} className="text-orange-500" />
                                        <h3 className="text-sm font-medium">Smart Automation</h3>
                                    </div>
                                    <p className="text-xs text-gray-600 dark:text-gray-400">Automated maintenance scheduling and intelligent alerts.</p>
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

            {/* Login Modal */}
            <Modal
                isOpen={showLoginModal}
                onClose={handleCloseModal}

                title="Log in to your account"
            >
                <LoginForm
                    onSuccess={handleLoginSuccess}
                    onClose={handleCloseModal}
                />
            </Modal>
        </div>
        </>
    );
};

export default Landing;