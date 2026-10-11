import { Link, useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();
  const role = localStorage.getItem("role");
  const roleName = localStorage.getItem("role_name");

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("role_name");
    sessionStorage.removeItem("token");
    navigate("/login");
  }

  return (
    <nav className="bg-zinc-900 p-4 flex justify-between items-center text-white">
      <div className="space-x-4 flex items-center">
        <Link to="/">Dashboard</Link>
        <Link to="/history">History</Link>
        <span className="text-xs text-zinc-400">{roleName || "User"}</span>
      </div>
      <button onClick={logout} className="text-red-400">Logout</button>
    </nav>
  );
}
