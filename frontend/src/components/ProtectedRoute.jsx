import { Navigate } from "react-router-dom";

/**
 * A wrapper component that requires auth to render its children.
 * If there is no 'access_token' in localStorage, it automatically redirects
 * the user to the /login page before mounting the protected content.
 */
// eslint-disable-next-line react/prop-types
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem("access_token");

  if (!token) {
    // They don't have a token, so redirect them to the login page immediately.
    // Replace prevents them from using the back button to try returning to this protected route
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
