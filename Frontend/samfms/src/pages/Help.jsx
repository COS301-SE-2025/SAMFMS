import React, {useState} from 'react';
import {Button} from '../components/ui/button';
import {HelpCircle, BookOpen, FileQuestion, Video, Info, Phone, ChevronDown, ChevronUp} from 'lucide-react';

const faqs = [
    {
        question: 'How do I reset my password?',
        answer: 'Go to your account settings and click on "Reset Password". Follow the instructions sent to your email.'
    },
    {
        question: 'Where can I view my drivers trip history?',
        answer: 'You can view your trip history from the Trips section in the sidebar. If you do not see this option, your role may not have access.'
    },
    {
        question: 'How do I assign a vehicle to a driver?',
        answer: 'Admins and Fleet Managers can assign vehicles to drivers from the Drivers or Vehicles management pages.'
    },
    {
        question: 'Can I export my reports?',
        answer: 'Yes, you can export reports from the Reports section if your role has permission.'
    },
    {
        question: 'Why do I only see certain menu items in the sidebar?',
        answer: 'The SAMFMS system uses role-based access control (RBAC). This means you only see the features and pages in the sidebar that your assigned role (such as Admin, Fleet Manager, or Driver) allows you to access. If you need access to additional features, please contact your system administrator.'
    }
];

const Help = () => {
    const [openIndex, setOpenIndex] = useState(null);
    const toggleFAQ = idx => {
        setOpenIndex(openIndex === idx ? null : idx);
    };
    return (
        <div className="min-h-screen bg-background relative">
            {/* SVG pattern background like Landing page */}
            <div
                className="absolute inset-0 z-0 opacity-10 pointer-events-none"
                style={{
                    backgroundImage: 'url("/logo/logo_icon_dark.svg")',
                    backgroundSize: '200px',
                    backgroundRepeat: 'repeat',
                    filter: 'blur(1px)',
                }}
            />
            <div className="relative z-10 container mx-auto py-8">
                <header className="mb-8">
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <HelpCircle size={28} />
                        Help Center
                    </h1>
                    <p className="text-muted-foreground mt-2">
                        Find guides, tutorials, and answers to frequently asked questions about SAMFMS.
                    </p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    {/* Quick help section */}
                    <div className="bg-card rounded-lg shadow-md p-6 border border-border">
                        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                            <BookOpen size={20} />
                            Getting Started
                        </h2>
                        <p className="text-muted-foreground mb-4">
                            New to SAMFMS? Check out these resources to help you get started:
                        </p>
                        <ul className="space-y-2 ml-6 list-disc text-foreground">
                            <li>System overview</li>
                            <li>User account setup</li>
                            <li>Basic navigation guide</li>
                            <li>Understanding permissions</li>
                        </ul>
                    </div>

                    {/* FAQ section */}
                    <div className="bg-card rounded-lg shadow-md p-6 border border-border">
                        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                            <FileQuestion size={20} />
                            Frequently Asked Questions
                        </h2>
                        <p className="text-muted-foreground mb-4">
                            Find quick answers to common questions:
                        </p>
                        <div className="divide-y divide-border">
                            {faqs.map((faq, idx) => (
                                <div key={idx}>
                                    <button
                                        className="w-full flex justify-between items-center py-3 text-left focus:outline-none"
                                        onClick={() => toggleFAQ(idx)}
                                    >
                                        <span className="font-medium text-foreground">{faq.question}</span>
                                        {openIndex === idx ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                                    </button>
                                    {openIndex === idx && (
                                        <div className="py-2 text-muted-foreground text-sm ml-2 animate-fade-in">
                                            {faq.answer}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-card rounded-lg shadow-md p-6 border border-border">
                        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                            <Video size={20} />
                            Video Tutorials
                        </h2>
                        <p className="text-muted-foreground">
                            Watch step-by-step guides on using different features of SAMFMS.
                        </p>
                    </div>

                    <div className="bg-card rounded-lg shadow-md p-6 border border-border">
                        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                            <Info size={20} />
                            User Manual
                        </h2>
                        <p className="text-muted-foreground">
                            Access the complete user manual for detailed information about the system.
                        </p>
                    </div>

                    <div className="bg-card rounded-lg shadow-md p-6 border border-border">
                        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                            <Phone size={20} />
                            Contact Support
                        </h2>
                        <p className="text-muted-foreground">
                            Need further assistance? Our support team is ready to help.
                        </p>
                        <Button className="mt-4" variant="outline">
                            Contact Support
                        </Button>
                    </div>
                </div>

                <div className="mt-8 p-4 bg-accent/10 rounded-lg border border-border">
                    <p className="text-sm text-center text-muted-foreground">
                        SAMFMS version 1.0 | Last updated: June 2025 | <Button variant="link" className="p-0 h-auto">View release notes</Button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Help;