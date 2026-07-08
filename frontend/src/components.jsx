import { NavLink } from "react-router-dom";
import { useState, useRef, useEffect } from "react";
import { cleanErrorMessage } from "./api";

export function StatusBadge({ status }) {
  return <span className={`status-badge status-${(status || "unknown").toLowerCase()}`}>
    <span className="bdot"></span>
    {status || "unknown"}
  </span>;
}

export function MetricCard({ label, value, delta, deltaType = "flat" }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {delta && <div className={`metric-delta ${deltaType}`}>{delta}</div>}
    </div>
  );
}

export function ProfileMenu({ user, onLogout, onSettings }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const initials = user?.display_name
    ? user.display_name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase()
    : user?.username?.slice(0, 2).toUpperCase() || "U";

  return (
    <div className={`profile-menu ${isOpen ? "is-open" : ""}`} ref={menuRef}>
      <button className="profile-trigger" onClick={() => setIsOpen(!isOpen)}>
        <div className="profile-trigger-avatar">
          {user?.avatar_url ? (
            <img src={user.avatar_url} alt="Avatar" />
          ) : (
            initials
          )}
        </div>
        <span className="profile-trigger-name">{user?.display_name || user?.username}</span>
        <span className="profile-trigger-caret"></span>
      </button>

      <div className="profile-dropdown">
        <div className="profile-dropdown-header">
          <div className="profile-trigger-avatar">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="Avatar" />
            ) : (
              initials
            )}
          </div>
          <div>
            <div className="profile-dropdown-name">{user?.display_name || user?.username}</div>
            <div className="profile-dropdown-email">{user?.email}</div>
          </div>
        </div>

        <div className="profile-dropdown-divider"></div>

        <button className="profile-dropdown-item" onClick={() => { setIsOpen(false); onSettings?.(); }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19 12a7 7 0 00-.2-1.6l2-1.5-2-3.4-2.3.9a7 7 0 00-2.7-1.6L13.4 2h-2.8l-.4 2.8a7 7 0 00-2.7 1.6l-2.3-.9-2 3.4 2 1.5A7 7 0 005 12"/>
          </svg>
          Configuración
        </button>

        <div className="profile-dropdown-divider"></div>

        <button className="profile-dropdown-item is-danger" onClick={() => { setIsOpen(false); onLogout?.(); }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
            <path d="M16 17l5-5-5-5"/>
            <path d="M21 12H9"/>
          </svg>
          Cerrar sesión
        </button>
      </div>
    </div>
  );
}

export function AppShell({ title, subtitle, actions, children, user, onLogout, onSettings }) {
  return (
    <div className="app-shell">
      <nav className="top-nav">
        <div className="brand">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
            <path d="M12 3L4 7.5v9L12 21l8-4.5v-9L12 3z"/>
          </svg>
          Protein Redesign
          <span className="brand-subtitle">Pipeline Console</span>
        </div>

        <div className="nav">
          <NavLink to="/" end className="nav-link">Dashboard</NavLink>
          <NavLink to="/projects" className="nav-link">Projects</NavLink>
          <NavLink to="/files" className="nav-link">My Files</NavLink>
          <NavLink to="/reports" className="nav-link">Reports</NavLink>
          <NavLink to="/documentation" className="nav-link">Docs</NavLink>
          <NavLink to="/tools" className="nav-link">Tools</NavLink>
          {user?.role === "admin" && <NavLink to="/monitoring" className="nav-link">Monitoring</NavLink>}
          <NavLink to="/about" className="nav-link">About</NavLink>
        </div>

        <ProfileMenu user={user} onLogout={onLogout} onSettings={onSettings} />
      </nav>

      <main className="main-panel">
        <header className="page-header">
          <div>
            <h1>{title}</h1>
            {subtitle && <p>{subtitle}</p>}
          </div>
          {actions && <div className="page-actions">{actions}</div>}
        </header>
        {children}
      </main>
    </div>
  );
}

export function Panel({ title, description, actions, children }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>{title}</h2>
          {description && <p>{description}</p>}
        </div>
        {actions}
      </div>
      <div className="panel-body">
        {children}
      </div>
    </section>
  );
}

export function PipelineCard({ pipeline }) {
  return (
    <div className="pipeline-card">
      <div className="pipeline-card-top">
        <div>
          <div className="eyebrow">{pipeline.project_name}</div>
          <div className="pipeline-title">Pipeline #{pipeline.pipeline_id}</div>
        </div>
        <StatusBadge status={pipeline.status} />
      </div>
      <div className="pipeline-meta">
        <div>Current stage: {pipeline.current_stage || "n/a"}</div>
        <div>Progress: {pipeline.progress.completed}/{pipeline.progress.total}</div>
      </div>
    </div>
  );
}

export function ExecutionTable({ rows, onOpen }) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Pipeline</th>
            <th>Status</th>
            <th>Current stage</th>
            <th>Progress</th>
            <th>Started</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.pipeline_id}>
              <td>
                <div className="table-primary">Pipeline #{row.pipeline_id}</div>
                <div className="table-secondary">{row.project_name}</div>
              </td>
              <td><StatusBadge status={row.status} /></td>
              <td>{row.current_stage || "n/a"}</td>
              <td>{row.progress.completed}/{row.progress.total}</td>
              <td>{row.started_at ? new Date(row.started_at).toLocaleString() : "n/a"}</td>
              <td>
                <button className="link-button" onClick={() => onOpen(row)}>Open</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function WorkerStatusPanel({ workers, system }) {
  return (
    <div className="worker-grid">
      {workers.map((worker) => (
        <div className="worker-card" key={worker.name}>
          <div className="worker-title">{worker.name}</div>
          <StatusBadge status={worker.status} />
          <div className="worker-caption">{worker.hostname || "No heartbeat yet"}</div>
          <div className="worker-caption">
            Last seen: {worker.last_seen ? new Date(worker.last_seen).toLocaleTimeString() : "n/a"}
          </div>
        </div>
      ))}
      {Object.entries(system).map(([key, value]) => (
        <div className="worker-card" key={key}>
          <div className="worker-title">{key}</div>
          <StatusBadge status={value} />
        </div>
      ))}
    </div>
  );
}

export function ToolsPanel({ tools }) {
  return (
    <div className="worker-grid">
      {tools.map((tool) => (
        <div className="worker-card" key={tool.name}>
          <div className="worker-title">{tool.name}</div>
          <StatusBadge status={tool.status || "available"} />
          <div className="worker-caption">{tool.description || "No description"}</div>
          <div className="worker-caption">Params: {tool.parameters?.length || 0}</div>
        </div>
      ))}
    </div>
  );
}

export function StageNode({ stage }) {
  return (
    <div className={`stage-node stage-${(stage.status || "pending").toLowerCase()}`}>
      <div className="stage-node-top">
        <div>
          <div className="eyebrow">Stage {stage.stage_order_index + 1}</div>
          <div className="stage-name">{stage.stage_name}</div>
        </div>
        <StatusBadge status={stage.status} />
      </div>
      <div className="stage-details">
        <div>Tool: {stage.tool}</div>
        <div>Retry count: {stage.retry_count}</div>
        <div>Task id: {stage.celery_task_id || "n/a"}</div>
      </div>
      {stage.error_message && <div className="error-box">{cleanErrorMessage(stage.error_message)}</div>}
    </div>
  );
}

export function ParameterFormGenerator({
  tool,
  values,
  projectFiles = [],
  uploadState = "",
  localId = "",
  onUploadFile,
  onChange,
}) {
  const visibleParameters = [...(tool?.parameters || [])]
    .filter((parameter) => !parameter.is_output)
    .filter((parameter) => parameter.name !== "output_dir")
    .sort((a, b) => (a.position ?? 999) - (b.position ?? 999));
  const primaryParameters = visibleParameters.filter(isPrimaryParameter);
  const advancedParameters = visibleParameters.filter((parameter) => !isPrimaryParameter(parameter));

  return (
    <div className="parameter-layout">
      <div className="parameter-stack">
        {primaryParameters.map((parameter) => {
          return renderParameterField(parameter, values, projectFiles, uploadState, localId, onUploadFile, onChange);
        })}
      </div>
      {advancedParameters.length ? (
        <details className="advanced-panel">
          <summary>Advanced parameters</summary>
          <div className="parameter-stack advanced-stack">
            {advancedParameters.map((parameter) =>
              renderParameterField(parameter, values, projectFiles, uploadState, localId, onUploadFile, onChange),
            )}
          </div>
        </details>
      ) : null}
    </div>
  );
}

function renderParameterField(parameter, values, projectFiles, uploadState, localId, onUploadFile, onChange) {
  const key = parameter.name;
  const currentValue = values[key] ?? parameter.default_value ?? (parameter.data_type === "bool" ? false : "");
  const inputType = parameter.data_type === "int" || parameter.data_type === "float" ? "number" : "text";
  const uploadKey = `${localId}:${key}`;
  const isPathParam = parameter.data_type === "file" || parameter.data_type === "directory";

  if (parameter.data_type === "bool") {
    return (
      <label key={key} className="field checkbox-field">
        <span>{parameter.ui_label || parameter.name}</span>
        <input
          type="checkbox"
          checked={Boolean(currentValue)}
          onChange={(event) => onChange(key, event.target.checked)}
        />
        {parameter.description && <small>{parameter.description}</small>}
      </label>
    );
  }

  if (isPathParam) {
    const matchingFiles = projectFiles.filter((file) => matchesProjectPathParameter(file, parameter));
    const uploadLabel = parameter.data_type === "directory" ? "Upload .zip" : "Upload file";
    return (
      <div key={key} className="field">
        <label>{parameter.ui_label || parameter.name}</label>
        <select
          value={currentValue}
          onChange={(event) => onChange(key, event.target.value)}
        >
          <option value="">Select uploaded file</option>
          {matchingFiles.map((file) => (
            <option key={file.relative_path} value={file.absolute_path}>
              {file.relative_path}
            </option>
          ))}
        </select>
        <div className="file-upload-row">
          <input
            type="file"
            accept={parameter.data_type === "directory" ? ".zip,application/zip" : undefined}
            onChange={(event) => onUploadFile?.(localId, key, event.target.files?.[0])}
          />
          <span className="table-secondary">{uploadLabel}</span>
          <span className="table-secondary">
            {uploadState === uploadKey ? "Uploading..." : currentValue.split(/[\\/]/).pop() || "No file selected"}
          </span>
        </div>
        {parameter.description && <small>{parameter.description}</small>}
      </div>
    );
  }

  return (
    <label key={key} className="field">
      <span>{parameter.ui_label || parameter.name}</span>
      <input
        type={inputType}
        value={currentValue}
        placeholder={parameter.format || parameter.name}
        onChange={(event) => onChange(key, event.target.value)}
      />
      {parameter.description && <small>{parameter.description}</small>}
    </label>
  );
}

function isPrimaryParameter(parameter) {
  if (!parameter.optional) return true;
  if (parameter.is_input) return true;
  return ["algorithm", "partners", "ligand_chain", "gen", "popsize", "mutp"].includes(parameter.name);
}

function matchesProjectPathParameter(file, parameter) {
  if (parameter.data_type === "directory") {
    return file.name.toLowerCase().endsWith(".zip");
  }
  const format = (parameter.format || "").toLowerCase();
  if (!format) return true;
  return file.name.toLowerCase().endsWith(`.${format}`);
}