import { Component } from "react";

// Catches unexpected rendering errors so one broken page doesn't blank the whole app
export default class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error("Unexpected UI error:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="container">
          <div className="error-message" role="alert">
            Something went wrong while displaying this page.
          </div>
          <button type="button" onClick={() => window.location.assign("/")}>
            Back to home
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
