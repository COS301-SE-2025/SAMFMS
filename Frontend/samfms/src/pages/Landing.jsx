import React, {useState, useEffect} from 'react';
import {Button} from '../components/ui/button';
import Modal from '../components/ui/Modal';
import LoginForm from '../components/auth/LoginForm';
import { TypewriterEffectSmooth } from '../components/ui/typewriter-effect';
import { Spotlight } from '../components/ui/spotlight-new';
import { Timeline } from '../components/ui/timeline';
import CardSwap, { Card } from '../components/ui/CardSwap';
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
    Github,
    Download,
    Smartphone
} from 'lucide-react';

const Landing = () => {
    const navigate = useNavigate();
    const [checkingStatus, setCheckingStatus] = useState(true);
    const [hasExistingUsers, setHasExistingUsers] = useState(null);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [currentHeadingIndex, setCurrentHeadingIndex] = useState(0);

    const headings = [
        [
            { text: "Smart" },
            { text: "Fleet", className: "text-blue-500 dark:text-blue-400" },
            { text: "Management", className: "text-blue-500 dark:text-blue-400" },
            { text: "at your" },
            { text: "fingertips" }
        ],
        [
            { text: "Optimize" },
            { text: "Vehicle", className: "text-green-500 dark:text-green-400" },
            { text: "Utilization", className: "text-green-500 dark:text-green-400" },
        ],
        [
            { text: "Track" },
            { text: "Assets", className: "text-purple-500 dark:text-purple-400" },
            { text: "in", className: "text-purple-500 dark:text-purple-400" },
            { text: "real-time" }
        ],
        [
            { text: "Streamline" },
            { text: "Operations", className: "text-orange-500 dark:text-orange-400" },
            { text: "effortlessly", className: "text-orange-500 dark:text-orange-400" }
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

    // Cycle through different headings
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentHeadingIndex((prevIndex) => (prevIndex + 1) % headings.length);
        }, 8000); // Change heading every 8 seconds

        return () => clearInterval(interval);
    }, [headings.length]);

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
        <div className="bg-background">
            {/* Hero Section - Fixed */}
            <div className="fixed top-0 left-0 w-full h-screen overflow-hidden bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 group z-10">
                <Spotlight 
                    className="top-0 left-0 w-full h-full"
                    gradientFirst="radial-gradient(68.54% 68.72% at 55.02% 31.46%, hsla(210, 100%, 85%, .12) 0, hsla(210, 100%, 55%, .04) 50%, hsla(210, 100%, 45%, 0) 80%)"
                    gradientSecond="radial-gradient(50% 50% at 50% 50%, hsla(210, 100%, 85%, .08) 0, hsla(210, 100%, 55%, .04) 80%, transparent 100%)"
                    gradientThird="radial-gradient(50% 50% at 50% 50%, hsla(210, 100%, 85%, .06) 0, hsla(210, 100%, 45%, .04) 80%, transparent 100%)"
                    width={800}
                    height={600}
                    smallWidth={400}
                    translateY={-200}
                    xOffset={200}
                />
                <div className="container mx-auto px-4 py-4 lg:py-8 relative z-10">
                    <div className="flex flex-col md:flex-row items-center justify-between">
                        <div className="w-full md:w-1/2 mb-12 md:mb-0">
                            <img
                                src="/logo/logo_horisontal_light.svg"
                                alt="SAMFMS Logo"
                                className="h-16 transition-all duration-300 dark:hidden"
                            />
                            <img
                                src="/logo/logo_horisontal_dark.svg"
                                alt="SAMFMS Logo"
                                className="h-16 transition-all duration-300 hidden dark:block"
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
                            <div className="flex flex-col items-center md:items-start gap-4">
                                <Button
                                    size="lg"
                                    onClick={handleGetStarted}
                                    className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-10 py-4 h-auto text-lg font-semibold flex items-center gap-3 rounded-xl shadow-lg hover:shadow-xl transform transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] focus:ring-4 focus:ring-blue-300 dark:focus:ring-blue-800 border-0 relative overflow-hidden group"
                                >
                                    <span className="relative z-10 flex items-center gap-3">
                                        {hasExistingUsers ? 'Login to Account' : 'Create First Account'}
                                        <ChevronRight size={20} className="group-hover:translate-x-1 transition-transform duration-200" />
                                    </span>
                                    <div className="absolute inset-0 bg-gradient-to-r from-blue-700 to-blue-800 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                                </Button>
                                
                                <div className="flex flex-wrap gap-3 justify-center md:justify-start">
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
                                    
                                    <Button
                                        variant="outline"
                                        size="lg"
                                        onClick={() => {
                                            const link = document.createElement('a');
                                            link.href = '/driverapp/SAMFMS-release.apk';
                                            link.download = 'SAMFMS-Driver-App.apk';
                                            document.body.appendChild(link);
                                            link.click();
                                            document.body.removeChild(link);
                                        }}
                                        className="border-2 border-green-300 dark:border-green-600 text-green-700 dark:text-green-300 hover:bg-green-50 dark:hover:bg-green-900 px-6 py-3 h-auto text-base font-medium flex items-center gap-3 rounded-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
                                    >
                                        <Smartphone size={20} />
                                        <Download size={16} />
                                        Driver App
                                    </Button>
                                </div>
                            </div>
                        </div>
                        
                        {/* Right side - Card Swap */}
                        <div className="w-full md:w-1/2 relative flex items-end justify-start min-h-[600px] pt-8">
                            <div className="relative w-full h-full -ml-8">
                                <CardSwap
                                    width={520}
                                    height={380}
                                    cardDistance={60}
                                    verticalDistance={80}
                                    delay={3000}
                                    pauseOnHover={false}
                                    easing="elastic"
                                >
                                    <Card>
                                        <div className="card-content">
                                            <img 
                                                src="/landingpage/vehiclemanagement.png" 
                                                alt="Vehicle Management Dashboard"
                                                className="w-full h-64 object-cover rounded-t-sm"
                                            />
                                            <div className="p-3">
                                                <div className="card-icon">
                                                    <Car size={20} />
                                                </div>
                                                <h3 className="card-title text-sm font-medium">Vehicle Management</h3>
                                                <p className="card-description text-xs">Comprehensive vehicle tracking with real-time location monitoring and fleet overview.</p>
                                            </div>
                                        </div>
                                    </Card>
                                    <Card>
                                        <div className="card-content">
                                            <img 
                                                src="/landingpage/driverbehaviourmonitoring.png" 
                                                alt="Driver Behaviour Monitoring"
                                                className="w-full h-64 object-cover rounded-t-sm"
                                            />
                                            <div className="p-3">
                                                <div className="card-icon">
                                                    <Shield size={20} />
                                                </div>
                                                <h3 className="card-title text-sm font-medium">Driver Safety</h3>
                                                <p className="card-description text-xs">Advanced driver behavior monitoring with safety scoring and violation tracking.</p>
                                            </div>
                                        </div>
                                    </Card>
                                    <Card>
                                        <div className="card-content">
                                            <img 
                                                src="/landingpage/maintenanceanalytics.png" 
                                                alt="Maintenance Analytics Dashboard"
                                                className="w-full h-64 object-cover rounded-t-sm"
                                            />
                                            <div className="p-3">
                                                <div className="card-icon">
                                                    <BarChart size={20} />
                                                </div>
                                                <h3 className="card-title text-sm font-medium">Analytics & Reports</h3>
                                                <p className="card-description text-xs">Comprehensive analytics dashboard with maintenance insights and performance metrics.</p>
                                            </div>
                                        </div>
                                    </Card>
                                    <Card>
                                        <div className="card-content">
                                            <img 
                                                src="/landingpage/tripscheduling.png" 
                                                alt="Trip Scheduling Interface"
                                                className="w-full h-64 object-cover rounded-t-sm"
                                            />
                                            <div className="p-3">
                                                <div className="card-icon">
                                                    <Zap size={20} />
                                                </div>
                                                <h3 className="card-title text-sm font-medium">Smart Trip Planning</h3>
                                                <p className="card-description text-xs">Intelligent trip scheduling with automated route optimization and resource allocation.</p>
                                            </div>
                                        </div>
                                    </Card>
                                    <Card>
                                        <div className="card-content">
                                            <img 
                                                src="/landingpage/customdashoard.png" 
                                                alt="Custom Dashboard Interface"
                                                className="w-full h-64 object-cover rounded-t-sm"
                                            />
                                            <div className="p-3">
                                                <div className="card-icon">
                                                    <Map size={20} />
                                                </div>
                                                <h3 className="card-title text-sm font-medium">Custom Dashboards</h3>
                                                <p className="card-description text-xs">Personalized dashboard experience with customizable widgets and real-time data visualization.</p>
                                            </div>
                                        </div>
                                    </Card>
                                </CardSwap>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Spacer to push content down initially */}
            <div className="h-screen"></div>

            {/* Content that scrolls over hero */}
            <div className="relative z-20 bg-background">
                {/* Timeline Section */}
                <Timeline data={[
                    {
                        title: "Vehicle Management",
                        content: (
                            <div>
                                <p className="mb-8 text-xs font-normal text-neutral-800 md:text-sm dark:text-neutral-200">
                                    Comprehensive vehicle tracking and management system with real-time GPS monitoring, fleet overview, and detailed vehicle information management.
                                </p>
                                <div className="mb-6">
                                    <div className="flex items-center gap-2 mb-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        <Car size={16} className="text-blue-500" />
                                        Complete vehicle inventory with detailed specifications
                                    </div>
                                    <div className="flex items-center gap-2 mb-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        <Map size={16} className="text-green-500" />
                                        Real-time GPS location tracking and status monitoring
                                    </div>
                                    <div className="flex items-center gap-2 mb-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        <Shield size={16} className="text-red-500" />
                                        Vehicle health monitoring and maintenance tracking
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <img
                                        src="/landingpage/vehiclemanagement.png"
                                        alt="Vehicle Management Dashboard"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/usermanagement.png"
                                        alt="User Management Interface"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/maintenancetracking.png"
                                        alt="Maintenance Tracking System"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/tripscheduling.png"
                                        alt="Trip Scheduling Interface"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                </div>
                            </div>
                        ),
                    },
                    {
                        title: "Analytics & Reporting",
                        content: (
                            <div>
                                <p className="mb-8 text-xs font-normal text-neutral-800 md:text-sm dark:text-neutral-200">
                                    Advanced analytics dashboard providing comprehensive insights into maintenance performance, driver behavior analysis, and operational efficiency metrics.
                                </p>
                                <div className="mb-6">
                                    <div className="flex items-center gap-2 mb-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        <BarChart size={16} className="text-purple-500" />
                                        Comprehensive maintenance analytics and reporting
                                    </div>
                                    <div className="flex items-center gap-2 mb-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        <Zap size={16} className="text-yellow-500" />
                                        Driver behavior scoring and violation tracking
                                    </div>
                                    <div className="flex items-center gap-2 mb-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        <Shield size={16} className="text-indigo-500" />
                                        Real-time performance metrics and KPIs
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <img
                                        src="/landingpage/maintenanceanalytics.png"
                                        alt="Maintenance Analytics Dashboard"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/driverbehaviourmonitoring.png"
                                        alt="Driver Behaviour Analytics"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/customdashoard.png"
                                        alt="Custom Dashboard Analytics"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/maintenancetracking.png"
                                        alt="Maintenance Tracking Reports"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                </div>
                            </div>
                        ),
                    },
                    {
                        title: "Driver App & User Management",
                        content: (
                            <div>
                                <p className="mb-4 text-xs font-normal text-neutral-800 md:text-sm dark:text-neutral-200">
                                    Comprehensive mobile driver application with user management system for seamless fleet operations and communication.
                                </p>
                                <div className="mb-8">
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Intuitive mobile driver application interface
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Comprehensive driver dashboard and profiles
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Built-in support and help system
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Advanced user management and permissions
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Role-based access control system
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <img
                                        src="/landingpage/driverapp.jpeg"
                                        alt="Driver Mobile Application"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/driverappdashboard.jpeg"
                                        alt="Driver App Dashboard"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/driverappprofile.jpeg"
                                        alt="Driver Profile Management"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/driverappsupport.jpeg"
                                        alt="Driver App Support System"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                </div>
                            </div>
                        ),
                    },
                    {
                        title: "Customizable Dashboard",
                        content: (
                            <div>
                                <p className="mb-4 text-xs font-normal text-neutral-800 md:text-sm dark:text-neutral-200">
                                    Personalized fleet management dashboard with comprehensive data visualization, real-time insights, and customizable interface.
                                </p>
                                <div className="mb-8">
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Comprehensive dashboard overview with KPIs
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Interactive data charts and analytics
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Customizable widgets and layouts
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Real-time fleet performance metrics
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Advanced filtering and data visualization
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <img
                                        src="/landingpage/customdashoard.png"
                                        alt="Custom Dashboard Overview"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/maintenanceanalytics.png"
                                        alt="Analytics Dashboard"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/driverbehaviourmonitoring.png"
                                        alt="Performance Monitoring"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/vehiclemanagement.png"
                                        alt="Vehicle Management View"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                </div>
                            </div>
                        ),
                    },
                    {
                        title: "Driver Analytics",
                        content: (
                            <div>
                                <p className="mb-4 text-xs font-normal text-neutral-800 md:text-sm dark:text-neutral-200">
                                    Advanced driver behavior monitoring and analytics with comprehensive safety insights and performance tracking.
                                </p>
                                <div className="mb-8">
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Real-time driver behavior monitoring and alerts
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Comprehensive safety scoring and assessment
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Mobile driver app with intuitive interface
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Performance trends and analytical insights
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Driver profile management and tracking
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <img
                                        src="/landingpage/driverbehaviourmonitoring.png"
                                        alt="Driver Behavior Monitoring"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/driverapp.jpeg"
                                        alt="Driver Mobile Application"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/driverappdashboard.jpeg"
                                        alt="Driver Analytics Dashboard"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/driverappprofile.jpeg"
                                        alt="Driver Profile Analytics"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                </div>
                            </div>
                        ),
                    },
                    {
                        title: "Maintenance Tracking",
                        content: (
                            <div>
                                <p className="mb-4 text-xs font-normal text-neutral-800 md:text-sm dark:text-neutral-200">
                                    Advanced maintenance management system with comprehensive analytics, scheduling automation, and detailed tracking capabilities.
                                </p>
                                <div className="mb-8">
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Comprehensive maintenance analytics and reporting
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Detailed maintenance tracking and history
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Automated scheduling and reminder system
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Cost analysis and budget optimization
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-neutral-700 md:text-sm dark:text-neutral-300">
                                        ✅ Predictive maintenance insights
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <img
                                        src="/landingpage/maintenanceanalytics.png"
                                        alt="Maintenance Analytics Dashboard"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/maintenancetracking.png"
                                        alt="Maintenance Tracking System"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/vehiclemanagement.png"
                                        alt="Vehicle Maintenance Overview"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                    <img
                                        src="/landingpage/tripscheduling.png"
                                        alt="Maintenance Scheduling"
                                        className="h-20 w-full rounded-lg object-cover shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] md:h-44 lg:h-60"
                                    />
                                </div>
                            </div>
                        ),
                    },
                ]} />

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
        </div>
    );
};

export default Landing;