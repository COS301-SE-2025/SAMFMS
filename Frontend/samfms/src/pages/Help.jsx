import React from 'react';
import {Button} from '../components/ui/button';
import {HelpCircle, BookOpen, FileQuestion, Video, Info, Phone} from 'lucide-react';

const Help = () => {
    return (
        <div className="container mx-auto py-8">
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
                    <ul className="space-y-2 ml-6 list-disc text-foreground">
                        <li>How do I reset my password?</li>
                        <li>Where can I view my trip history?</li>
                        <li>How do I assign a vehicle to a driver?</li>
                        <li>Can I export my reports?</li>
                    </ul>
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
    );
};

export default Help;