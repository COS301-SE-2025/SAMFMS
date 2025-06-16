import React from 'react';

class AuthErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error
    console.error('Auth Error Boundary caught an error:', error, errorInfo);

    this.setState({
      error: error,
      errorInfo: errorInfo,
    });

    // Log error to monitoring service
    this.logErrorToService(error, errorInfo);
  }

  logErrorToService(error, errorInfo) {
    // In a real app, you'd send this to your error monitoring service
    console.log('Logging error to monitoring service:', {
      error: error.toString(),
      errorInfo: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleLogout = async () => {
    try {
      const { logout } = await import('../backend/api/auth');
      await logout();
      window.location.href = '/login';
    } catch (error) {
      console.error('Failed to logout:', error);
      // Force logout by clearing storage and redirecting
      localStorage.clear();
      sessionStorage.clear();
      window.location.href = '/login';
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full">
              <svg
                className="w-6 h-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>

            <div className="mt-4 text-center">
              <h3 className="text-lg font-medium text-gray-900">Authentication Error</h3>
              <p className="mt-2 text-sm text-gray-500">
                Something went wrong with the authentication system. This could be due to:
              </p>
              <ul className="mt-2 text-sm text-gray-500 text-left list-disc list-inside">
                <li>Network connectivity issues</li>
                <li>Server maintenance</li>
                <li>Session expiration</li>
                <li>Browser compatibility issues</li>
              </ul>
            </div>

            <div className="mt-6 flex flex-col space-y-3">
              <button
                onClick={this.handleRetry}
                className="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Try Again
              </button>

              <button
                onClick={this.handleLogout}
                className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Logout & Restart
              </button>
            </div>

            {process.env.NODE_ENV === 'development' && (
              <details className="mt-4">
                <summary className="text-sm text-gray-500 cursor-pointer">
                  Technical Details (Development Only)
                </summary>
                <div className="mt-2 p-3 bg-gray-100 rounded text-xs text-gray-700 overflow-auto max-h-40">
                  <div>
                    <strong>Error:</strong> {this.state.error && this.state.error.toString()}
                  </div>
                  <div className="mt-2">
                    <strong>Stack:</strong>
                  </div>
                  <pre className="whitespace-pre-wrap">
                    {this.state.errorInfo && this.state.errorInfo.componentStack}
                  </pre>
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default AuthErrorBoundary;
