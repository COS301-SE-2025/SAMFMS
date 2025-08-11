import React, { useState } from 'react';
import TrackingMapWithSidebar from '../components/tracking/TrackingMapWithSidebar';
import FadeIn from '../components/ui/FadeIn';

const Tracking = () => {
  const [error, setError] = useState(null);

  return (
    <FadeIn delay={0.1}>
      <div className="relative w-full h-full">
        <div
          className="absolute inset-0 z-0 opacity-10 pointer-events-none"
          style={{
            backgroundImage: 'url("/logo/logo_icon_dark.svg")',
            backgroundSize: '200px',
            backgroundRepeat: 'repeat',
            filter: 'blur(1px)',
          }}
          aria-hidden="true"
        />

        <div className="relative z-10 h-full">
          {error && (
            <FadeIn delay={0.3}>
              <div className="absolute top-4 left-4 right-4 z-20 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                {error}
              </div>
            </FadeIn>
          )}

          {/* Map with Sidebar */}
          <FadeIn delay={0.4}>
            <TrackingMapWithSidebar />
          </FadeIn>
        </div>
      </div>
    </FadeIn>
  );
};

export default Tracking;
