import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { testCoreService } from '../backend/api/plugins';
import { useAuth, ROLES } from '../components/auth/RBACUtils';
import PluginTable from '../components/PluginTable';
import FadeIn from '../components/ui/FadeIn';

const Plugins = () => {
  const { hasRole } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  // Check if user has admin access
  const isAdmin = hasRole(ROLES.ADMIN);

  // Load plugins on component mount
  useEffect(() => {
    const initializePlugins = async () => {
      try {
        setLoading(true);
        setError('');

        // Test Core service connectivity first
        console.log('Testing Core service connectivity...');
        const healthCheck = await testCoreService();
        if (!healthCheck.success) {
          throw new Error(`Core service is not accessible: ${healthCheck.error}`);
        }
        console.log('Core service is accessible');
      } catch (err) {
        console.error('Error loading plugins:', err);
      } finally {
        setLoading(false);
      }
    };

    initializePlugins();
  }, [isAdmin]);

  const refreshPlugins = async () => {
    try {
      setRefreshing(true);
      setError('');

      // Test connectivity
      const healthCheck = await testCoreService();
      if (!healthCheck.success) {
        throw new Error(`Core service is not accessible: ${healthCheck.error}`);
      }
    } catch (err) {
      setError('Failed to refresh plugins: ' + err.message);
      console.error('Error refreshing plugins:', err);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex justify-center items-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p>Loading plugins...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-background to-muted/20">
      {/* Background pattern */}
      <div
        className="absolute inset-0 z-0 opacity-5 pointer-events-none"
        style={{
          backgroundImage: 'url("/logo/logo_icon_dark.svg")',
          backgroundSize: '300px',
          backgroundRepeat: 'repeat',
          filter: 'blur(1px)',
        }}
        aria-hidden="true"
      />

      {/* Content */}
      <FadeIn delay={0.1} className="relative z-10 container mx-auto py-8">
        <FadeIn delay={0.2}>
          <div className="flex items-center justify-between p-4 border-b border-border">
            <div>
              <h1 className="text-2xl font-bold">Plugin Management</h1>
              <p className="text-muted-foreground">Manage system plugins and extensions</p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                onClick={refreshPlugins}
                variant="outline"
                disabled={refreshing}
                title="Refresh plugin status and connectivity"
              >
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </Button>
            </div>
          </div>
        </FadeIn>

        {/* Plugin Health Overview */}
        <FadeIn delay={0.3}>
          <div className="mb-8">
            <div className="bg-card/80 backdrop-blur-sm rounded-xl p-6 border border-border/50 shadow-lg">
              <PluginTable />
            </div>
          </div>
        </FadeIn>

        {error && (
          <FadeIn delay={0.4}>
            <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-xl text-destructive backdrop-blur-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-destructive rounded-full flex-shrink-0"></div>
                <span className="font-medium">Error:</span>
                {error}
              </div>
            </div>
          </FadeIn>
        )}
      </FadeIn>
    </div>
  );
};

export default Plugins;
