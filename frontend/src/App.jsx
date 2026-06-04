import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import UploadClaim from './pages/UploadClaim';
import ClaimStatus from './pages/ClaimStatus';
import Appeals from './pages/Appeals';
import ReviewQueue from './pages/ReviewQueue';
import AdminDashboard from './pages/AdminDashboard';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="navbar">
          <NavLink to="/" className="navbar-brand">
            <span>🏥</span> Plum OPD Adjudicator
          </NavLink>
          <ul className="navbar-links">
            <li><NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''} end>Submit Claim</NavLink></li>
            <li><NavLink to="/status" className={({ isActive }) => isActive ? 'active' : ''}>Status</NavLink></li>
            <li><NavLink to="/appeals" className={({ isActive }) => isActive ? 'active' : ''}>Appeals</NavLink></li>
            <li><NavLink to="/review" className={({ isActive }) => isActive ? 'active' : ''}>Review Queue</NavLink></li>
            <li><NavLink to="/admin" className={({ isActive }) => isActive ? 'active' : ''}>Dashboard</NavLink></li>
          </ul>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<UploadClaim />} />
            <Route path="/status" element={<ClaimStatus />} />
            <Route path="/appeals" element={<Appeals />} />
            <Route path="/review" element={<ReviewQueue />} />
            <Route path="/admin" element={<AdminDashboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
