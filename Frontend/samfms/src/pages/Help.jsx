import React, {useState} from 'react';
import {Button} from '../components/ui/button';
import FadeIn from '../components/ui/FadeIn';
import {
  HelpCircle,
  BookOpen,
  FileQuestion,
  Video,
  Info,
  Phone,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

const faqs = [
  {
    question: 'How do I reset my password?',
    answer:
      'Go to your account settings and click on "Reset Password". Follow the instructions sent to your email.',
  },
  {
    question: 'Where can I view my drivers trip history?',
    answer:
      'You can view your trip history from the Trips section in the sidebar. If you do not see this option, your role may not have access.',
  },
  {
    question: 'How do I assign a vehicle to a driver?',
    answer:
      'Admins and Fleet Managers can assign vehicles to drivers from the Drivers or Vehicles management pages.',
  },
  {
    question: 'How do I manage dashboard widgets?',
    answer: 'To add widgets, click the "Add Widget" button and select from available options. Resize widgets by dragging the corners, and move them by clicking and dragging the widget header to your desired position on the dashboard.',
  },
  {
    question: 'Why do I only see certain menu items in the sidebar?',
    answer:
      'The SAMFMS system uses role-based access control (RBAC). This means you only see the features and pages in the sidebar that your assigned role (such as Admin, Fleet Manager, or Driver) allows you to access. If you need access to additional features, please contact your system administrator.',
  },
];

const gettingStartedItems = [
  {
    title: 'System overview',
    content:
      'The SAMFMS (Smart Automated Fleet Management System) is a microservices-based platform designed to streamline fleet operations through modular, service-oriented architecture. It provides centralized management of vehicles, drivers, assignments, trips, maintenance, GPS tracking, and security, with all services accessible via a RESTful API gateway. Each service—Management, Maintenance, GPS, Trip Planning, and Security—operates independently but communicates seamlessly through standardized messaging contracts, ensuring resilience, scalability, and fault tolerance. The system enforces robust authentication and role-based access control while supporting real-time notifications, analytics, and monitoring to enhance operational efficiency and decision-making.',
  },
  {
    title: 'User account setup',
    content:
      'When setting up accounts in the system, the very first registered user is automatically granted administrator rights, establishing the initial point of control. Authorized users with access to the User Management page can create additional accounts through the sidebar interface. From this page, three distinct green plus buttons allow the creation of new Admin, Fleet Manager, or Driver accounts. Selecting one of these options opens a dedicated form where the relevant user details can be entered and submitted, ensuring streamlined onboarding and role-based access control.',
  },
  {
    title: 'Basic navigation guide',
    content:
      'Navigation through the system is managed via the sidebar menu, which allows users to switch between core pages. Available pages include the Dashboard, Vehicles Page, Drivers Page, Driver Behavior Page, Tracking Page, Trips Page, Maintenance Page, User Management, Plugins, Account, and Help. The visibility of these pages depends on the user\'s role and permissions; if a page does not appear in the sidebar, the account is not authorized to access it.',
  },
  {
    title: 'Understanding permissions',
    content:
      'When you first log into the system, the very first account created will automatically become the Admin. From there, admins (or anyone with permission to manage users) can go to the User Management page using the sidebar. On this page, you\'ll see three green plus buttons—one for creating a new Admin, one for a Fleet Manager, and one for a Driver. Simply click the button for the type of account you want to create, fill in the form with the user\'s details, and save it. The sidebar is how you\'ll move around the system, and the pages you see depend on your role. Admins see everything, fleet managers see fewer pages, and drivers see the least. If you don\'t see a page in your sidebar, your account doesn\'t have permission to use it.',
  },
];

const Help = () => {
  const [openFAQIndex, setOpenFAQIndex] = useState(null);
  const [openGettingStartedIndex, setOpenGettingStartedIndex] = useState(null);

  const toggleFAQ = idx => {
    setOpenFAQIndex(openFAQIndex === idx ? null : idx);
  };

  const toggleGettingStarted = idx => {
    setOpenGettingStartedIndex(openGettingStartedIndex === idx ? null : idx);
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
        <FadeIn delay={0.1}>
          <header className="mb-8">
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <HelpCircle size={28} />
              Help Center
            </h1>
            <p className="text-muted-foreground mt-2">
              Find guides, tutorials, and answers to frequently asked questions about SAMFMS.
            </p>
          </header>
        </FadeIn>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Getting Started section */}
          <FadeIn delay={0.2}>
            <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg p-6 h-full flex flex-col">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <BookOpen size={20} />
                Getting Started
              </h2>
              <p className="text-muted-foreground mb-4">
                New to SAMFMS? Check out these resources to help you get started:
              </p>
              <div className="divide-y divide-border flex-1">
                {gettingStartedItems.map((item, idx) => (
                  <div key={idx}>
                    <button
                      className="w-full flex justify-between items-center py-3 text-left focus:outline-none"
                      onClick={() => toggleGettingStarted(idx)}
                    >
                      <span className="font-medium text-foreground">{item.title}</span>
                      {openGettingStartedIndex === idx ? (
                        <ChevronUp className="h-5 w-5 flex-shrink-0" />
                      ) : (
                        <ChevronDown className="h-5 w-5 flex-shrink-0" />
                      )}
                    </button>
                    {openGettingStartedIndex === idx && (
                      <FadeIn delay={0.1} direction="up">
                        <div className="py-2 text-muted-foreground text-sm ml-2">{item.content}</div>
                      </FadeIn>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </FadeIn>

          {/* FAQ section */}
          <FadeIn delay={0.3}>
            <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg p-6 h-full flex flex-col">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <FileQuestion size={20} />
                Frequently Asked Questions
              </h2>
              <p className="text-muted-foreground mb-4">Find quick answers to common questions:</p>
              <div className="divide-y divide-border flex-1">
                {faqs.map((faq, idx) => (
                  <div key={idx}>
                    <button
                      className="w-full flex justify-between items-center py-3 text-left focus:outline-none"
                      onClick={() => toggleFAQ(idx)}
                    >
                      <span className="font-medium text-foreground">{faq.question}</span>
                      {openFAQIndex === idx ? (
                        <ChevronUp className="h-5 w-5 flex-shrink-0" />
                      ) : (
                        <ChevronDown className="h-5 w-5 flex-shrink-0" />
                      )}
                    </button>
                    {openFAQIndex === idx && (
                      <FadeIn delay={0.1} direction="up">
                        <div className="py-2 text-muted-foreground text-sm ml-2">{faq.answer}</div>
                      </FadeIn>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </FadeIn>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-1 gap-6">
          {/* User Manual section */}
          <FadeIn delay={0.5}>
            <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Info size={20} />
                User Manual
              </h2>
              <p className="text-muted-foreground mb-4">
                Access the complete user manual for detailed information about the system.
              </p>
              <Button
                onClick={() => window.open('/user_manual/SAMFMS User Manual.pdf', '_blank')}
                className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
              >
                <BookOpen size={16} className="mr-2" />
                Open User Manual
              </Button>
            </div>
          </FadeIn>
        </div>

        <FadeIn delay={0.7}>
          <div className="mt-8 p-4 bg-accent/10 rounded-lg border border-border">
            <p className="text-sm text-center text-muted-foreground">
              SAMFMS version 1.0 | Last updated: June 2025 |{' '}
              <Button variant="link" className="p-0 h-auto">
                View release notes
              </Button>
            </p>
          </div>
        </FadeIn>
      </div>
    </div>
  );
};

export default Help;
