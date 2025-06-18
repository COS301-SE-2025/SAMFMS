import React from 'react';
import {Button} from '../components/ui/button';
import ColorPalette from '../components/ColorPalette';
import DashboardLayoutToolbar from '../components/DashboardLayoutToolbar';

const Help = () => {
    return (
        <div className="container mx-auto py-8">
            <header className="mb-8">
                <h1 className="text-4xl font-bold">Help & Getting Started</h1>
                <p className="text-muted-foreground">
                    Learn how to use the SAMFMS platform and get the most out of your fleet management experience.
                </p>
            </header>

            {/* Layout toolbar below the top toolbar */}
            <DashboardLayoutToolbar />

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <HelpCard
                    title="Navigating the Dashboard"
                    content="A quick overview of the dashboard layout and main features."
                    footer="Read more"
                />
                <HelpCard
                    title="Managing Vehicles"
                    content="How to add, edit, and monitor your fleet vehicles."
                    footer="Vehicle management guide"
                />
                <HelpCard
                    title="Trip Planning"
                    content="Step-by-step instructions for planning and tracking trips."
                    footer="Trip planning tutorial"
                />
                <HelpCard
                    title="Maintenance Scheduling"
                    content="Learn how to schedule and track vehicle maintenance."
                    footer="Maintenance help"
                />
                <HelpCard
                    title="Driver Management"
                    content="Add, assign, and monitor drivers in your fleet."
                    footer="Driver management tips"
                />
                <HelpCard
                    title="Frequently Asked Questions"
                    content="Find answers to common questions about SAMFMS."
                    footer="View FAQ"
                />
            </div>

            <div className="mt-12 border-t border-border pt-8">
                <ColorPalette />
            </div>
        </div>
    );
};

// A simple card component for the help page
const HelpCard = ({title, content, footer}) => {
    return (
        <div className="bg-card rounded-lg shadow-md p-6 border border-border">
            <h2 className="text-xl font-semibold mb-4">{title}</h2>
            <p className="text-foreground mb-6">{content}</p>
            <div className="border-t border-border pt-4">
                <Button
                    variant="ghost"
                    className="p-0 h-auto text-sm text-muted-foreground hover:text-foreground"
                >
                    {footer}
                </Button>
            </div>
        </div>
    );
};

export default Help;