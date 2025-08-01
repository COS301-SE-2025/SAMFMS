import React, { Component } from 'react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to an error reporting service
    console.error('Error caught by boundary:', error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo,
    });
  }

  render() {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return (
        <div className="min-h-screen flex justify-center items-center bg-primary-100">
          <div className="text-center p-8 max-w-lg bg-white rounded-lg shadow-lg">
            <div className="text-red-600 text-5xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-red-600 mb-4">Something went wrong</h2>
            <p className="text-gray-700 mb-6">
              The application encountered an unexpected error. Please try refreshing the page.
            </p>
            {this.state.error && (
              <div className="bg-gray-100 p-4 rounded-lg text-left mb-4 max-h-40 overflow-auto">
                <p className="text-red-600 font-mono text-sm mb-2">{this.state.error.toString()}</p>
                <details className="text-gray-600">
                  <summary className="cursor-pointer text-sm mb-1">Stack trace</summary>
                  <pre className="text-xs whitespace-pre-wrap">
                    {this.state.errorInfo && this.state.errorInfo.componentStack}
                  </pre>
                </details>
              </div>
            )}
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-primary-700 text-white rounded hover:bg-primary-800"
              >
                Reload Page
              </button>
              <button
                onClick={() => {
                  localStorage.clear(); // Clear cookies using our eraseCookie function for consistency
                  ['token', 'refresh_token', 'user', 'permissions', 'preferences'].forEach(
                    cookieName => {
                      document.cookie =
                        cookieName +
                        '=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT; Secure; SameSite=Strict;';
                    }
                  );
                  window.location.href = '/login';
                }}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Reset & Login
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
