import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Overview", end: true },
  { to: "/entities", label: "Entities" },
  { to: "/products", label: "Products" },
  { to: "/search", label: "Search" },
  { to: "/reviews", label: "Reviews" },
  { to: "/changes", label: "Changes" },
  { to: "/agents/content", label: "Content Agent" },
  { to: "/agents/gtm", label: "GTM Agent" }
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">AB</span>
        <span>Analytos Brain</span>
      </div>
      <nav aria-label="Main navigation">
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end} className={({ isActive }) => (isActive ? "active" : undefined)}>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
