import { useState } from "react";
import Login from "./pages/Login";
import Orders from "./pages/Orders";
import Upload from "./pages/Upload";
import { isLoggedIn, clearToken } from "./auth";
import "./App.css";

type Tab = "orders" | "upload";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(isLoggedIn);
  const [tab, setTab] = useState<Tab>("orders");
  const [refresh, setRefresh] = useState(0);

  function handleLogout() {
    clearToken();
    setLoggedIn(false);
  }

  function handleOrderCreated() {
    setTab("orders");
    setRefresh((r) => r + 1);
  }

  if (!loggedIn) {
    return <Login onLogin={() => setLoggedIn(true)} />;
  }

  return (
    <div className="app">
      <header className="header">
        <span className="header-title">Document Extractor</span>
        <nav>
          <button
            className={tab === "orders" ? "nav-btn active" : "nav-btn"}
            onClick={() => setTab("orders")}
          >
            Orders
          </button>
          <button
            className={tab === "upload" ? "nav-btn active" : "nav-btn"}
            onClick={() => setTab("upload")}
          >
            Upload
          </button>
        </nav>
        <button className="btn-logout" onClick={handleLogout}>
          Sign out
        </button>
      </header>
      <main className="main">
        {tab === "orders" && <Orders refresh={refresh} />}
        {tab === "upload" && <Upload onOrderCreated={handleOrderCreated} />}
      </main>
    </div>
  );
}
