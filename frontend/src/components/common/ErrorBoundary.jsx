import React, { Component } from 'react';
import Button from './Button';
import './ErrorBoundary.css';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  // eslint-disable-next-line no-unused-vars
  static getDerivedStateFromError(_error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo,
    });

    // 에러 로깅 (프로덕션에서는 서버로 전송 가능)
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    // 홈으로 리디렉션
    window.location.href = '/';
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-boundary__content">
            <div className="error-boundary__icon">
              <svg
                width="64"
                height="64"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <h1 className="error-boundary__title">앗, 문제가 발생했어요!</h1>
            <p className="error-boundary__message">
              예기치 않은 오류가 발생했습니다.
              <br />
              잠시 후 다시 시도해 주세요.
            </p>
            <div className="error-boundary__actions">
              <Button variant="secondary" onClick={this.handleReload}>
                🔄 새로고침
              </Button>
              <Button onClick={this.handleReset}>🏠 홈으로 가기</Button>
            </div>
            {import.meta.env.DEV && this.state.error && (
              <details className="error-boundary__details">
                <summary>개발자 정보</summary>
                <pre>
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
