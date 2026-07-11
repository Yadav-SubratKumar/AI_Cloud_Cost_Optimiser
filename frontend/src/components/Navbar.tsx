import {
  Link,
  useNavigate
} from "react-router-dom";

export default function Navbar() {
  const navigate =
    useNavigate();

  function logout() {
    localStorage.removeItem(
      "token"
    );

    navigate("/login");
  }

  return (
    <nav className="bg-zinc-900 p-4 flex justify-between">
      <div className="space-x-4">
        <Link to="/">
          Dashboard
        </Link>

        <Link to="/history">
          History
        </Link>
      </div>

      <button
        onClick={logout}
        className="text-red-400"
      >
        Logout
      </button>
    </nav>
  );
}