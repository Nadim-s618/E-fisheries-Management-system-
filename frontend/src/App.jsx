import { BrowserRouter, Navigate, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthProvider';
import { useAuth } from './context/useAuth';
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import FishStorePage from './pages/FishStorePage';
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
// import WaterQualityPage from './pages/WaterQualityPage';


function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="route-loading">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/fish-store" element={<FishStorePage />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/signup" element={<AuthPage mode="signup" />} />
          <Route path="/register" element={<AuthPage mode="signup" />} />
          <Route
            path="/dashboard"
            element={(
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            )}
          />
          <Route
            path="/profile"
            element={(
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            )}
          />
          {/* <Route path="/water-quality" element={<WaterQualityPage />} /> */}
          {/* Add more routes here as you build new pages, e.g.: */}
          {/* <Route path="/feeding" element={<FeedingPage />} /> */}
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
