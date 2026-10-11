import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import Report from "./pages/Report";

function getToken() {
  return localStorage.getItem("token") || sessionStorage.getItem("token");
}

function Protected({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const token = getToken();
  if (!token) return <Navigate to="/login" replace />;
  const role = localStorage.getItem("role");
  if (roles && role && !roles.includes(role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/" element={<Protected><Dashboard /></Protected>} />
        <Route path="/history" element={<Protected><History /></Protected>} />
        <Route path="/report" element={<Protected><Report /></Protected>} />
      </Routes>
    </BrowserRouter>
  );
}
