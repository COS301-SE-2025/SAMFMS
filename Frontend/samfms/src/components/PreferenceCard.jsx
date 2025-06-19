import React from 'react';

const PreferenceCard = ({ title, description, icon, children, className = '', actions }) => {
  return (
    <div
      className={`bg-card p-6 rounded-lg shadow-sm border border-border hover:shadow-md transition-shadow ${className}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {icon && <div className="flex-shrink-0 text-primary">{icon}</div>}
          <div>
            <h3 className="text-lg font-medium text-foreground">{title}</h3>
            {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
          </div>
        </div>

        {actions && <div className="flex items-center space-x-2">{actions}</div>}
      </div>

      <div className="space-y-4">{children}</div>
    </div>
  );
};

export default PreferenceCard;
