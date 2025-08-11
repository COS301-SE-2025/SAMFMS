import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

class WidgetErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Widget error caught by boundary:', error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo,
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    // Force component re-render by updating key
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-card border border-border rounded-lg shadow-sm overflow-hidden h-full flex flex-col">
          {/* Widget Header */}
          <div className="flex items-center justify-between p-3 border-b border-border bg-card/50 flex-shrink-0">
            <h3 className="font-medium text-card-foreground truncate">
              {this.props.widgetTitle || 'Widget Error'}
            </h3>
          </div>

          {/* Error Content */}
          <div className="p-4 flex-grow flex flex-col items-center justify-center">
            <div className="bg-destructive/10 border border-destructive text-destructive rounded-lg p-4 w-full max-w-sm text-center">
              <AlertTriangle className="h-8 w-8 mx-auto mb-3" />
              <h4 className="font-medium mb-2">Widget Failed to Load</h4>
              <p className="text-sm mb-4 opacity-90">
                This widget encountered an error and couldn't be displayed.
              </p>

              <div className="flex flex-col gap-2">
                <button
                  onClick={this.handleRetry}
                  className="flex items-center justify-center gap-2 px-3 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 text-sm"
                >
                  <RefreshCw size={14} />
                  Retry
                </button>

                {process.env.NODE_ENV === 'development' && (
                  <details className="mt-2">
                    <summary className="text-xs cursor-pointer opacity-75">
                      Error Details (Dev Only)
                    </summary>
                    <div className="mt-2 text-xs text-left bg-background rounded p-2 opacity-75">
                      <div className="font-mono break-all">
                        {this.state.error && this.state.error.toString()}
                      </div>
                      {this.state.errorInfo && (
                        <pre className="mt-1 text-xs whitespace-pre-wrap">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      )}
                    </div>
                  </details>
                )}
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default WidgetErrorBoundary;
