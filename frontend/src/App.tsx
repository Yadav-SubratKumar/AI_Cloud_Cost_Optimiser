import {
  BrowserRouter,
  Routes,
  Route,
  Navigate
} from "react-router-dom";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import Report from "./pages/Report";

function Protected({
  children,
}: any) {
  const token =
    localStorage.getItem("token");

  if (!token) {
    return (
      <Navigate to="/login" />
    );
  }

  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/signup"
          element={<Signup />}
        />

        <Route
          path="/"
          element={
            <Protected>
              <Dashboard />
            </Protected>
          }
        />

        <Route
          path="/history"
          element={
            <Protected>
              <History />
            </Protected>
          }
        />

        <Route
          path="/report"
          element={
            <Protected>
              <Report />
            </Protected>
          }
        />

      </Routes>
    </BrowserRouter>
  );
}