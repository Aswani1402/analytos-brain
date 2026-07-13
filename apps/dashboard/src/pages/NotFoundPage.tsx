import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">404</p>
          <h1>Page not found</h1>
        </div>
      </div>
      <Link to="/">Return to overview</Link>
    </div>
  );
}
