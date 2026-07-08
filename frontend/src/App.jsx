import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";

import {
  addGroupMember,
  approvePipeline,
  cleanErrorMessage,
  createGroup,
  createPipeline,
  createProject,
  deactivateProfile,
  deletePipeline,
  downloadProjectFile,
  downloadProjectReport,
  downloadPipelineReport,
  downloadStageArtifact,
  getAssetUrl,
  getExecution,
  getExecutionStages,
  getGroups,
  getMe,
  getMonitoringSummary,
  getProfile,
  getDocumentationDownloadUrl,
  getDocumentationEntries,
  getPipeline,
  getProjectFiles,
  getProjectOutputs,
  getProjectReportsOverview,
  getPipelines,
  getProjects,
  getServiceTypes,
  getStageArtifacts,
  getTools,
  getUserGuideUrl,
  getPipelineReportOverview,
  login,
  register,
  removeGroupMember,
  retryStage,
  runPipeline,
  updateGroupMember,
  updateProfile,
  uploadAvatar,
  uploadProjectFile,
} from "./api";
import { clearToken, isAuthenticated, setToken } from "./auth";
import {
  AppShell,
  ExecutionTable,
  MetricCard,
  Panel,
  ParameterFormGenerator,
  PipelineCard,
  StageNode,
  StatusBadge,
  ToolsPanel,
} from "./components";

function usePolling(loader, deps, intervalMs = 6000) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        if (loading) {
          setLoading(true);
        }
        const result = await loader();
        if (!active) return;
        setData(result);
        setError("");
      } catch (err) {
        if (!active) return;
        setError(err.message || "Unknown error");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();
    const id = window.setInterval(load, intervalMs);
    return () => {
      active = false;
      window.clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error, loading, setData };
}

function ProtectedLayout({ children, title, subtitle, actions, user }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    clearToken();
    window.location.href = "/login";
  };

  const handleSettings = () => {
    navigate("/profile");
  };

  return (
    <AppShell
      title={title}
      subtitle={subtitle}
      actions={actions}
      user={user}
      onLogout={handleLogout}
      onSettings={handleSettings}
    >
      {children}
    </AppShell>
  );
}

function AuthShell({ eyebrow, title, description, icon, children }) {
  return (
    <div className="login-page">
      <div className="login-panel register-panel">
        <div className="login-header">
          <div className="login-icon">{icon}</div>
          <div className="eyebrow">{eyebrow}</div>
        </div>
        <h1>{title}</h1>
        <p>{description}</p>
        {children}
      </div>
    </div>
  );
}

function LoginPage({ onAuthenticated }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("aisha@example.com");
  const [password, setPassword] = useState("12345678");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const payload = await login(email, password);
      setToken(payload.access_token);
      await onAuthenticated();
      navigate("/");
    } catch (err) {
      setError(err.message || "No se pudo iniciar sesion");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      eyebrow="Pipeline Console"
      title="Scientific Workflow Control Plane"
      description="Orchestrate, monitor, and debug bioinformatic pipelines from a single operator console."
      icon="PC"
    >
      <form className="form-stack" onSubmit={handleSubmit}>
        <label className="field">
          <span>Email</span>
          <input
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="usuario@ejemplo.com"
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Contrasena"
          />
        </label>
        {error ? <div className="error-box">{error}</div> : null}
        <button className="btn btn-primary btn-md" disabled={submitting}>
          {submitting ? "Ingresando..." : "Entrar"}
        </button>
        <button
          type="button"
          className="btn btn-secondary btn-md"
          onClick={() => navigate("/register")}
        >
          Crear cuenta
        </button>
      </form>
    </AuthShell>
  );
}

function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (form.password !== form.confirmPassword) {
      setError("Las contrasenas no coinciden.");
      return;
    }

    setSubmitting(true);
    try {
      await register({
        username: form.username.trim(),
        email: form.email.trim(),
        password: form.password,
      });
      setSuccess("Cuenta creada correctamente. Redirigiendo al login...");
      setForm({
        username: "",
        email: "",
        password: "",
        confirmPassword: "",
      });
      window.setTimeout(() => navigate("/login"), 900);
    } catch (err) {
      setError(err.message || "No se pudo registrar el usuario");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      eyebrow="Nuevo usuario"
      title="Create your operator account"
      description="Register a user to access projects, launch staged executions, and monitor the complete lifecycle."
      icon="RX"
    >
      <form className="form-stack" onSubmit={handleSubmit}>
        <div className="auth-grid">
          <label className="field">
            <span>Username</span>
            <input
              value={form.username}
              onChange={(event) => updateField("username", event.target.value)}
              placeholder="aisha"
            />
          </label>
          <label className="field">
            <span>Email</span>
            <input
              value={form.email}
              onChange={(event) => updateField("email", event.target.value)}
              placeholder="usuario@ejemplo.com"
            />
          </label>
        </div>
        <div className="auth-grid">
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={form.password}
              onChange={(event) => updateField("password", event.target.value)}
              placeholder="Minimo 8 caracteres"
            />
          </label>
          <label className="field">
            <span>Confirm password</span>
            <input
              type="password"
              value={form.confirmPassword}
              onChange={(event) => updateField("confirmPassword", event.target.value)}
              placeholder="Repite la contrasena"
            />
          </label>
        </div>
        {error ? <div className="error-box">{error}</div> : null}
        {success ? <div className="success-box">{success}</div> : null}
        <div className="auth-actions">
          <button className="btn btn-primary btn-md" disabled={submitting}>
            {submitting ? "Creando..." : "Crear cuenta"}
          </button>
          <button type="button" className="btn btn-secondary btn-md" onClick={() => navigate("/login")}>
            Volver al login
          </button>
        </div>
      </form>
    </AuthShell>
  );
}

function DashboardPage({ user }) {
  const navigate = useNavigate();
  const { data, error, loading } = usePolling(
    async () => {
      if (user?.role === "admin") {
        const [summary, tools] = await Promise.all([getMonitoringSummary(), getTools()]);
        return { ...summary, tools, mode: "admin" };
      }
      const projects = await getProjects();
      const pipelinesByProject = await Promise.all(projects.map((project) => getPipelines(project.id)));
      const flattened = pipelinesByProject.flat();
      return {
        mode: "user",
        kpis: {
          pipelines_active: flattened.filter((pipeline) => ["running", "waiting_for_approval"].includes(pipeline.status)).length,
          executions_in_progress: flattened.filter((pipeline) => pipeline.status === "running").length,
          recent_failures: flattened.filter((pipeline) => pipeline.status === "failed").length,
        },
        pipelines: flattened.map((pipeline) => ({
          pipeline_id: pipeline.id,
          project_id: pipeline.project_id,
          project_name: projects.find((project) => project.id === pipeline.project_id)?.name || `Project ${pipeline.project_id}`,
          version: pipeline.version,
          status: pipeline.status,
          current_stage: null,
          progress: { completed: 0, total: 0 },
          started_at: pipeline.started_at,
          finished_at: pipeline.finished_at,
        })),
        recent_failures: [],
        tools: await getTools(),
      };
    },
    [user?.role],
    5000
  );

  return (
    <ProtectedLayout
      title="Dashboard"
      subtitle="Operational overview of pipelines, stage tools and recent failures"
      user={user}
    >
      {error ? <div className="error-box">{error}</div> : null}
      <div className="metrics-grid">
        <MetricCard label="Active pipelines" value={data?.kpis?.pipelines_active ?? "--"} />
        <MetricCard label="Running executions" value={data?.kpis?.executions_in_progress ?? "--"} />
        <MetricCard label="Recent failures" value={data?.kpis?.recent_failures ?? "--"} />
        <MetricCard label="Tools available" value={data?.tools?.length ?? "--"} />
      </div>
      <div className="dashboard-grid">
        <Panel title="Pipeline executions" description="Pipelines ordered by recent activity">
          {loading && !data ? <div className="empty-state">Loading dashboard...</div> : null}
          {data?.pipelines?.length ? (
            <ExecutionTable
              rows={data.pipelines}
              onOpen={(row) => navigate(`/projects/${row.project_id}/pipelines/${row.pipeline_id}`)}
            />
          ) : (
            <div className="empty-state">No pipelines yet.</div>
          )}
        </Panel>
        <div className="stacked-panels">
          <Panel title="Recent failures" description="Latest broken stages and their messages">
            <div className="failure-list">
              {(data?.recent_failures || []).map((failure) => (
                <div className="failure-item" key={failure.stage_execution_id}>
                  <div className="failure-title">
                    <span>{failure.stage_name}</span>
                    <StatusBadge status="failed" />
                  </div>
                  <div className="table-secondary">Pipeline #{failure.pipeline_id} - {failure.tool}</div>
                  <div className="failure-message">{cleanErrorMessage(failure.error_message || "No error message stored.")}</div>
                </div>
              ))}
              {!data?.recent_failures?.length ? <div className="empty-state">{user?.role === "admin" ? "No recent failures." : "Recent failures are available in admin observability."}</div> : null}
            </div>
          </Panel>
          <Panel title="Available stage tools" description="Tools imported into the system for pipeline stages">
            <ToolsPanel tools={data?.tools || []} />
          </Panel>
        </div>
      </div>
    </ProtectedLayout>
  );
}

function ProfilePage({ user }) {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [groups, setGroups] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [groupForm, setGroupForm] = useState({ name: "", description: "" });
  const [memberForm, setMemberForm] = useState({ identifier: "", role: "member" });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let active = true;

    async function loadProfileData() {
      setLoading(true);
      setError("");

      try {
        const [profileData, groupsData] = await Promise.all([getProfile(), getGroups()]);
        if (!active) return;
        setProfile(profileData);
        setDisplayName(profileData.display_name || "");
        setGroups(groupsData);
        setSelectedGroupId((current) => current || String(groupsData[0]?.id || ""));
      } catch (err) {
        if (!active) return;
        setError(err.message || "No se pudo cargar los datos del perfil");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadProfileData();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedGroupId && groups.length) {
      setSelectedGroupId(String(groups[0].id));
    }
  }, [groups, selectedGroupId]);

  const selectedGroup = groups.find((group) => String(group.id) === String(selectedGroupId));
  const canManageSelectedGroup = selectedGroup?.current_user_role && selectedGroup.current_user_role !== "member";

  function mergeGroup(updatedGroup) {
    setGroups((current) => current.map((group) => (group.id === updatedGroup.id ? updatedGroup : group)));
  }

  async function reloadGroups() {
    try {
      const refreshed = await getGroups();
      setGroups(refreshed);
      if (!selectedGroupId) {
        setSelectedGroupId(String(refreshed[0]?.id || ""));
      }
    } catch (err) {
      setError(err.message || "No se pudo actualizar la lista de grupos");
    }
  }

  async function handleProfileSave(event) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      const updated = await updateProfile({ display_name: displayName });
      setProfile(updated);
      setSuccess("Perfil actualizado correctamente");
    } catch (err) {
      setError(err.message || "No se pudo actualizar el perfil");
    } finally {
      setBusy(false);
    }
  }

  async function handleAvatarUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      const updated = await uploadAvatar(file);
      setProfile(updated);
      setSuccess("Avatar actualizado");
    } catch (err) {
      setError(err.message || "No se pudo subir el avatar");
    } finally {
      event.target.value = "";
      setBusy(false);
    }
  }

  async function handleDeactivateAccount() {
    if (!window.confirm("¿Deseas desactivar tu cuenta? Esta acción cerrará tu sesión.")) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      await deactivateProfile();
      clearToken();
      navigate("/login");
    } catch (err) {
      setError(err.message || "No se pudo desactivar la cuenta");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateGroup(event) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    setSuccess("");

    try {
      const created = await createGroup(groupForm);
      await reloadGroups();
      setSelectedGroupId(String(created.id));
      setGroupForm({ name: "", description: "" });
      setSuccess("Grupo creado correctamente");
    } catch (err) {
      setError(err.message || "No se pudo crear el grupo");
    } finally {
      setBusy(false);
    }
  }

  async function handleAddGroupMember(event) {
    event.preventDefault();
    if (!selectedGroup) return;
    if (busy) return;
    setBusy(true);
    setError("");
    setSuccess("");

    try {
      const updated = await addGroupMember(selectedGroup.id, memberForm);
      mergeGroup(updated);
      setMemberForm({ identifier: "", role: "member" });
      setSuccess("Miembro agregado correctamente");
    } catch (err) {
      setError(err.message || "No se pudo agregar el miembro");
    } finally {
      setBusy(false);
    }
  }

  async function handleUpdateMemberRole(userId, newRole) {
    if (!selectedGroup) return;
    if (busy) return;
    setBusy(true);
    setError("");
    setSuccess("");

    try {
      const updated = await updateGroupMember(selectedGroup.id, userId, { role: newRole });
      mergeGroup(updated);
      setSuccess("Rol de miembro actualizado correctamente");
    } catch (err) {
      setError(err.message || "No se pudo actualizar el rol");
    } finally {
      setBusy(false);
    }
  }

  async function handleRemoveMember(userId) {
    if (!selectedGroup) return;
    if (!window.confirm("¿Eliminar este miembro del grupo?")) return;
    if (busy) return;
    setBusy(true);
    setError("");
    setSuccess("");

    try {
      await removeGroupMember(selectedGroup.id, userId);
      await reloadGroups();
      setSuccess("Miembro eliminado correctamente");
    } catch (err) {
      setError(err.message || "No se pudo eliminar el miembro");
    } finally {
      setBusy(false);
    }
  }

  return (
    <ProtectedLayout
      title="Perfil"
      subtitle="Administra tu perfil, avatar y grupos de trabajo colaborativos"
      user={user}
    >
      {error ? <div className="error-box">{error}</div> : null}
      {success ? <div className="success-box">{success}</div> : null}
      {loading && !profile ? <div className="empty-state">Cargando información del perfil...</div> : null}

      <div className="dashboard-grid">
        <Panel title="Configuración de perfil" description="Actualiza tu nombre visible y avatar">
          <div className="profile-summary-grid">
            <div>
              <div className="eyebrow">Cuenta</div>
              <div className="pipeline-title">{profile?.display_name || profile?.username || "Usuario"}</div>
              <div className="table-secondary">{profile?.email}</div>
              <div className="table-secondary">Rol: {profile?.role}</div>
              <div className="table-secondary">Proyectos: {profile?.project_count ?? 0}</div>
            </div>
            <div className="profile-avatar-wrap">
              {profile?.avatar_url ? (
                <img className="profile-avatar" src={getAssetUrl(profile.avatar_url)} alt="Avatar de perfil" />
              ) : (
                <div className="profile-avatar placeholder">{(profile?.display_name || profile?.username || "U").charAt(0).toUpperCase()}</div>
              )}
            </div>
          </div>
          <form className="form-stack" onSubmit={handleProfileSave}>
            <label className="field">
              <span>Nombre visible</span>
              <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
            </label>
            <div className="file-upload-row">
              <label className="btn btn-secondary btn-sm upload-button">
                Cambiar avatar
                <input type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={handleAvatarUpload} />
              </label>
              <button className="btn btn-primary btn-md" type="submit" disabled={busy}>
                Guardar perfil
              </button>
              <button className="btn btn-destructive btn-md" type="button" onClick={handleDeactivateAccount} disabled={busy}>
                Desactivar cuenta
              </button>
            </div>
          </form>
        </Panel>

        <Panel title="Grupos de trabajo" description="Tus grupos compartidos y permisos de equipo">
          {groups.length ? (
            <div className="pipeline-list">
              {groups.map((group) => (
                <button
                  key={group.id}
                  className={`pipeline-list-item ${String(group.id) === String(selectedGroupId) ? "active" : ""}`}
                  onClick={() => setSelectedGroupId(String(group.id))}
                >
                  <div>
                    <div className="table-primary">{group.name}</div>
                    <div className="table-secondary">{group.description || "Sin descripción"}</div>
                  </div>
                  <div className="documentation-meta">
                    <span className="status-badge status-pending"><span className="bdot"></span>{group.current_user_role}</span>
                    <span className="table-secondary">{group.members.length} miembros</span>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="empty-state compact">Aún no formas parte de ningún grupo.</div>
          )}
        </Panel>
      </div>

      <div className="dashboard-grid">
        <Panel title="Crear grupo" description="Crea un grupo de trabajo colaborativo">
          <form className="form-stack" onSubmit={handleCreateGroup}>
            <label className="field">
              <span>Nombre del grupo</span>
              <input
                value={groupForm.name}
                onChange={(event) => setGroupForm((current) => ({ ...current, name: event.target.value }))}
              />
            </label>
            <label className="field">
              <span>Descripción</span>
              <textarea
                value={groupForm.description}
                onChange={(event) => setGroupForm((current) => ({ ...current, description: event.target.value }))}
              />
            </label>
            <button className="btn btn-primary btn-md" type="submit" disabled={busy}>
              Crear grupo
            </button>
          </form>
        </Panel>

        <Panel title="Detalles del grupo" description={selectedGroup ? `Miembros y roles de ${selectedGroup.name}` : "Selecciona un grupo para ver sus miembros"}>
          {!selectedGroup ? (
            <div className="empty-state compact">Selecciona un grupo de la lista para ver detalles.</div>
          ) : (
            <>
              <div className="summary-list">
                <div>Rol en el grupo: {selectedGroup.current_user_role}</div>
                <div>Creado por: {selectedGroup.created_by_user_id}</div>
                <div>Miembros: {selectedGroup.members.length}</div>
              </div>
              <div className="pipeline-list">
                {selectedGroup.members.map((member) => (
                  <div key={member.user_id} className="pipeline-list-item">
                    <div>
                      <div className="table-primary">{member.display_name || member.username}</div>
                      <div className="table-secondary">{member.email}</div>
                    </div>
                    <div className="member-row">
                      <select
                        value={member.role}
                        disabled={!canManageSelectedGroup || member.user_id === profile?.id}
                        onChange={(event) => handleUpdateMemberRole(member.user_id, event.target.value)}
                      >
                        <option value="owner">owner</option>
                        <option value="admin">admin</option>
                        <option value="member">member</option>
                      </select>
                      {canManageSelectedGroup && member.user_id !== profile?.id ? (
                        <button className="btn btn-destructive btn-sm" onClick={() => handleRemoveMember(member.user_id)}>
                          Eliminar
                        </button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
              {canManageSelectedGroup ? (
                <form className="form-stack" onSubmit={handleAddGroupMember}>
                  <label className="field">
                    <span>Agregar miembro (username o email)</span>
                    <input
                      value={memberForm.identifier}
                      onChange={(event) => setMemberForm((current) => ({ ...current, identifier: event.target.value }))}
                      placeholder="usuario@ejemplo.com"
                    />
                  </label>
                  <label className="field">
                    <span>Rol</span>
                    <select
                      value={memberForm.role}
                      onChange={(event) => setMemberForm((current) => ({ ...current, role: event.target.value }))}
                    >
                      <option value="member">member</option>
                      <option value="admin">admin</option>
                      <option value="owner">owner</option>
                    </select>
                  </label>
                  <button className="btn btn-primary btn-md" type="submit" disabled={busy || !memberForm.identifier.trim()}>
                    Agregar miembro
                  </button>
                </form>
              ) : (
                <div className="empty-state compact">No tienes permiso para administrar este grupo.</div>
              )}
            </>
          )}
        </Panel>
      </div>
    </ProtectedLayout>
  );
}

function ProjectsPage({ user }) {
  const navigate = useNavigate();
  const [projectForm, setProjectForm] = useState({ name: "", description: "", group_id: "" });
  const [pipelineVersion, setPipelineVersion] = useState({});
  const [deleteConfirmKey, setDeleteConfirmKey] = useState("");
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  const { data, loading } = usePolling(async () => {
    const [projects, groups] = await Promise.all([getProjects(), getGroups()]);
    const pipelinesByProject = await Promise.all(
      projects.map(async (project) => ({
        projectId: project.id,
        pipelines: await getPipelines(project.id),
      })),
    );
    return { projects, groups, pipelinesByProject };
  }, [refreshKey], 9000);

  async function handleCreateProject(event) {
    event.preventDefault();
    setError("");
    try {
      await createProject({
        name: projectForm.name,
        description: projectForm.description,
        group_id: projectForm.group_id ? Number(projectForm.group_id) : null,
      });
      setProjectForm({ name: "", description: "", group_id: "" });
      setRefreshKey((value) => value + 1);
    } catch (err) {
      setError(err.message || "No se pudo crear el proyecto");
    }
  }

  async function handleCreatePipeline(projectId) {
    setError("");
    try {
      await createPipeline(projectId, {
        version: pipelineVersion[projectId] || "v1",
        parameters: {},
      });
      setPipelineVersion((current) => ({ ...current, [projectId]: "" }));
      setRefreshKey((value) => value + 1);
    } catch (err) {
      setError(err.message || "No se pudo crear el pipeline");
    }
  }

  async function handleDeletePipeline(projectId, pipelineId) {
    const confirmKey = `${projectId}:${pipelineId}`;
    if (deleteConfirmKey !== confirmKey) {
      setDeleteConfirmKey(confirmKey);
      return;
    }

    setError("");
    try {
      await deletePipeline(projectId, pipelineId);
      setDeleteConfirmKey("");
      setRefreshKey((value) => value + 1);
    } catch (err) {
      setError(err.message || "No se pudo eliminar el pipeline");
    }
  }

  return (
    <ProtectedLayout
      title="Projects"
      subtitle="Organize pipelines by project and launch execution flows from there"
      user={user}
    >
      <div className="two-column-layout">
        <Panel title="Create project" description="Create a container for related workflows">
          <form className="form-stack" onSubmit={handleCreateProject}>
            <label className="field">
              <span>Name</span>
              <input
                value={projectForm.name}
                onChange={(event) => setProjectForm((current) => ({ ...current, name: event.target.value }))}
              />
            </label>
            <label className="field">
              <span>Description</span>
              <textarea
                value={projectForm.description}
                onChange={(event) => setProjectForm((current) => ({ ...current, description: event.target.value }))}
              />
            </label>
            <label className="field">
              <span>Workspace</span>
              <select
                value={projectForm.group_id}
                onChange={(event) => setProjectForm((current) => ({ ...current, group_id: event.target.value }))}
              >
                <option value="">Personal project</option>
                {(data?.groups || [])
                  .filter((group) => ["owner", "admin"].includes(group.current_user_role))
                  .map((group) => (
                    <option key={group.id} value={group.id}>{group.name}</option>
                  ))}
              </select>
            </label>
            {error ? <div className="error-box">{error}</div> : null}
            <button className="btn btn-primary btn-md">Create project</button>
          </form>
        </Panel>
        <Panel title="Project inventory" description="Projects, pipelines and overall state">
          {loading && !data ? <div className="empty-state">Loading projects...</div> : null}
          <div className="project-list">
            {(data?.projects || []).map((project) => {
              const pipelineBundle = data?.pipelinesByProject?.find((item) => item.projectId === project.id);
              const pipelines = pipelineBundle?.pipelines || [];
              return (
                <div className="project-card" key={project.id}>
                  <div className="project-card-header">
                    <div>
                      <div className="pipeline-title">{project.name}</div>
                      <div className="table-secondary">
                        {project.description || "No description"}
                        {project.group_id ? ` · Group #${project.group_id}` : " · Personal"}
                      </div>
                    </div>
                    <div className="table-secondary">{pipelines.length} pipelines</div>
                  </div>
                  <div className="inline-form">
                    <input
                      placeholder="Pipeline version"
                      value={pipelineVersion[project.id] || ""}
                      onChange={(event) => setPipelineVersion((current) => ({ ...current, [project.id]: event.target.value }))}
                    />
                    <button className="btn btn-secondary btn-md" onClick={() => handleCreatePipeline(project.id)}>
                      Add pipeline
                    </button>
                  </div>
                  <div className="pipeline-list">
                    {pipelines.map((pipeline) => {
                      const confirmKey = `${project.id}:${pipeline.id}`;
                      const needsDeleteConfirm = deleteConfirmKey === confirmKey;
                      return (
                        <div key={pipeline.id} className="pipeline-row-item">
                          <button
                            className="pipeline-list-item pipeline-row-main"
                            onClick={() => navigate(`/projects/${project.id}/pipelines/${pipeline.id}`)}
                          >
                            <div>
                              <div className="table-primary">Pipeline #{pipeline.id}</div>
                              <div className="table-secondary">{pipeline.version || "no version"}</div>
                            </div>
                            <StatusBadge status={pipeline.status} />
                          </button>
                          <button
                            className={`btn btn-destructive btn-sm ${needsDeleteConfirm ? "is-confirming" : ""}`}
                            onClick={() => handleDeletePipeline(project.id, pipeline.id)}
                          >
                            {needsDeleteConfirm ? "Confirm delete" : "Delete"}
                          </button>
                        </div>
                      );
                    })}
                    {!pipelines.length ? <div className="empty-state compact">No pipelines yet.</div> : null}
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>
      </div>
    </ProtectedLayout>
  );
}

function PipelineDetailPage({ user }) {
  const { projectId, pipelineId } = useParams();
  const [serviceTypes, setServiceTypes] = useState([]);
  const [tools, setTools] = useState([]);
  const [composerStages, setComposerStages] = useState([]);
  const [pauseBetweenStages, setPauseBetweenStages] = useState(false);
  const [error, setError] = useState("");
  const [selectedStageId, setSelectedStageId] = useState(null);
  const [retryStageId, setRetryStageId] = useState("");
  const [retryParamsByStage, setRetryParamsByStage] = useState({});
  const [artifacts, setArtifacts] = useState([]);
  const [uploadingField, setUploadingField] = useState("");
  const [approvalParamsByStage, setApprovalParamsByStage] = useState({});
  const [refreshKey, setRefreshKey] = useState(0);

  const { data, loading } = usePolling(async () => {
    const [pipeline, execution, stages, toolList, typeList, projectFiles] = await Promise.all([
      getPipeline(projectId, pipelineId),
      getExecution(pipelineId),
      getExecutionStages(pipelineId),
      getTools(),
      getServiceTypes(),
      getProjectFiles(projectId),
    ]);
    setTools(toolList);
    setServiceTypes(typeList);
    return { pipeline, execution, stages, toolList, typeList, projectFiles };
  }, [projectId, pipelineId, refreshKey], 5000);

  const selectedStage = useMemo(
    () => data?.stages?.find((stage) => stage.id === selectedStageId) || data?.stages?.[0] || null,
    [data, selectedStageId],
  );
  const stageTypeOptions = useMemo(() => getStageTypeOptions(serviceTypes, tools), [serviceTypes, tools]);
  const executionStatus = data?.execution?.status || data?.pipeline?.status || "idle";
  const approvalWaiting = executionStatus === "waiting_for_approval";
  const selectedStageTool = useMemo(
    () => tools.find((item) => item.id === Number(selectedStage?.tool_id)) || null,
    [tools, selectedStage?.tool_id],
  );
  const selectedStageApprovalParams = selectedStage
    ? approvalParamsByStage[selectedStage.id] || {
        ...buildDefaultParams(selectedStageTool, data?.projectFiles || []),
        ...(selectedStage.params || {}),
      }
    : {};
  const retryableStages = useMemo(
    () => (data?.stages || []).filter((stage) => ["completed", "failed"].includes(stage.status)),
    [data?.stages],
  );
  const selectedRetryStage = useMemo(
    () => retryableStages.find((stage) => String(stage.id) === String(retryStageId)) || retryableStages[0] || null,
    [retryStageId, retryableStages],
  );
  const retryStageTool = useMemo(
    () => tools.find((item) => item.id === Number(selectedRetryStage?.tool_id)) || null,
    [tools, selectedRetryStage?.tool_id],
  );
  const retryStageParams = selectedRetryStage
    ? retryParamsByStage[selectedRetryStage.id] || {
        ...buildDefaultParams(retryStageTool, data?.projectFiles || []),
        ...(selectedRetryStage.params || {}),
      }
    : {};
  
  useEffect(() => {
    let cancelled = false;
    async function loadArtifacts() {
      if (!selectedStage?.id) {
        setArtifacts([]);
        return;
      }
      try {
        const nextArtifacts = await getStageArtifacts(selectedStage.id);
        if (!cancelled) {
          setArtifacts(nextArtifacts);
        }
      } catch {
        if (!cancelled) {
          setArtifacts([]);
        }
      }
    }
    loadArtifacts();
    return () => {
      cancelled = true;
    };
  }, [selectedStage?.id, (selectedStage?.output_files || []).join("|"), selectedStage?.status]);

  useEffect(() => {
    if (!selectedStage || selectedStage.status !== "waiting_for_approval") return;
    setApprovalParamsByStage((current) => {
      if (current[selectedStage.id]) return current;
      return {
        ...current,
        [selectedStage.id]: {
          ...buildDefaultParams(selectedStageTool, data?.projectFiles || []),
          ...(selectedStage.params || {}),
        },
      };
    });
  }, [data?.projectFiles, selectedStage, selectedStageTool]);

  useEffect(() => {
    if (!retryStageId && retryableStages[0]?.id) {
      setRetryStageId(String(retryableStages[0].id));
    }
  }, [retryStageId, retryableStages]);

  useEffect(() => {
    if (!selectedRetryStage) return;
    setRetryParamsByStage((current) => {
      if (current[selectedRetryStage.id]) return current;
      return {
        ...current,
        [selectedRetryStage.id]: {
          ...buildDefaultParams(retryStageTool, data?.projectFiles || []),
          ...(selectedRetryStage.params || {}),
        },
      };
    });
  }, [data?.projectFiles, selectedRetryStage, retryStageTool]);

  function addComposerStage() {
    const defaultStageName = stageTypeOptions[0]?.name || "refinement";
    const defaultTool = getToolsForStageName(tools, serviceTypes, defaultStageName)[0] || tools[0];
    setComposerStages((current) => [
      ...current,
      {
        localId: crypto.randomUUID(),
        stageType: defaultStageName,
        toolId: defaultTool?.id || "",
        stageName: resolveStageName(defaultTool, serviceTypes) || defaultStageName,
        params: buildDefaultParams(defaultTool, data?.projectFiles || []),
      },
    ]);
  }

  function updateComposerStage(localId, patch) {
    setComposerStages((current) =>
      current.map((stage) => (stage.localId === localId ? { ...stage, ...patch } : stage)),
    );
  }

  function removeComposerStage(localId) {
    setComposerStages((current) => current.filter((stage) => stage.localId !== localId));
  }

  async function handleUploadForStage(localId, parameterName, file) {
    if (!file) return;
    const uploadKey = `${localId}:${parameterName}`;
    setUploadingField(uploadKey);
    setError("");
    try {
      const uploaded = await uploadProjectFile(projectId, file, `pipeline_${pipelineId}`);
      setComposerStages((current) =>
        current.map((stage) =>
          stage.localId === localId
            ? { ...stage, params: { ...stage.params, [parameterName]: uploaded.absolute_path } }
            : stage,
        ),
      );
    } catch (err) {
      setError(err.message || "No se pudo subir el archivo");
    } finally {
      setUploadingField("");
    }
  }

  async function handleUploadForApproval(localId, parameterName, file) {
    if (!file || !selectedStage) return;
    const uploadKey = `${localId}:${parameterName}`;
    setUploadingField(uploadKey);
    setError("");
    try {
      const uploaded = await uploadProjectFile(projectId, file, `pipeline_${pipelineId}`);
      setApprovalParamsByStage((current) => ({
        ...current,
        [selectedStage.id]: {
          ...(current[selectedStage.id] || selectedStageApprovalParams),
          [parameterName]: uploaded.absolute_path,
        },
      }));
    } catch (err) {
      setError(err.message || "No se pudo subir el archivo");
    } finally {
      setUploadingField("");
    }
  }

  async function handleUploadForRetry(localId, parameterName, file) {
    if (!file || !selectedRetryStage) return;
    const uploadKey = `${localId}:${parameterName}`;
    setUploadingField(uploadKey);
    setError("");
    try {
      const uploaded = await uploadProjectFile(projectId, file, `pipeline_${pipelineId}`);
      setRetryParamsByStage((current) => ({
        ...current,
        [selectedRetryStage.id]: {
          ...(current[selectedRetryStage.id] || retryStageParams),
          [parameterName]: uploaded.absolute_path,
        },
      }));
    } catch (err) {
      setError(err.message || "No se pudo subir el archivo");
    } finally {
      setUploadingField("");
    }
  }

  async function handleLaunch() {
    setError("");
    try {
      const payload = {
        pause_between_stages: pauseBetweenStages,
        stage_order: composerStages.map((stage) => {
          const tool = tools.find((item) => item.id === Number(stage.toolId));
          return {
            stage_name: stage.stageName,
            tool_id: Number(stage.toolId),
            tool: tool?.name || "",
            params: stage.params,
          };
        }),
      };
      await runPipeline(projectId, pipelineId, payload);
      setComposerStages([]);
    } catch (err) {
      setError(err.message || "No se pudo lanzar el pipeline");
    }
  }

  async function handleApprove() {
    if (!approvalWaiting) {
      setError("La aprobacion solo esta disponible cuando el pipeline esta esperando aprobacion.");
      return;
    }
    setError("");
    try {
      await approvePipeline(pipelineId, {
        params: selectedStageApprovalParams,
      });
    } catch (err) {
      setError(err.message || "No se pudo aprobar la siguiente etapa");
    }
  }

  async function handleRetry() {
    if (!selectedRetryStage) {
      setError("Selecciona una etapa ejecutada para relanzarla.");
      return;
    }
    setError("");
    try {
      await retryStage(pipelineId, {
        stage_execution_id: Number(selectedRetryStage.id),
        stage_order_index: Number(selectedRetryStage.stage_order_index),
        new_params: retryStageParams,
      });
      setRefreshKey((value) => value + 1);
    } catch (err) {
      setError(err.message || "No se pudo reenviar la etapa");
    }
  }

  return (
    <ProtectedLayout
      title={`Pipeline #${pipelineId}`}
      subtitle="Execution viewer, launcher and stage-level inspection"
      user={user}
    >
      {error ? <div className="error-box">{error}</div> : null}
      {loading && !data ? <div className="empty-state">Loading pipeline...</div> : null}
      <div className="pipeline-detail-grid">
        <div className="stacked-panels">
          <Panel title="Pipeline state" description="Current orchestration status">
            <div className="pipeline-summary-grid">
              <div>
                <div className="eyebrow">Version</div>
                <div className="pipeline-title">{data?.pipeline?.version || "n/a"}</div>
              </div>
              <div>
                <div className="eyebrow">Pipeline status</div>
                <StatusBadge status={executionStatus} />
              </div>
              <div>
                <div className="eyebrow">Pause between stages</div>
                <div>{String(data?.execution?.pause_between_stages ?? false)}</div>
              </div>
            </div>
            <div className="stage-list">
              {(data?.stages || []).map((stage) => (
                <button key={stage.id} className="stage-button-reset" onClick={() => setSelectedStageId(stage.id)}>
                  <StageNode stage={stage} />
                </button>
              ))}
            </div>
          </Panel>

          <Panel title="Execution composer" description="Build a new run from imported tools and their contracts">
            <div className="composer-toolbar">
              <label className="checkbox-inline">
                <input
                  type="checkbox"
                  checked={pauseBetweenStages}
                  onChange={(event) => setPauseBetweenStages(event.target.checked)}
                />
                Pause between stages
              </label>
              <button className="btn btn-primary btn-md" disabled={!composerStages.length} onClick={handleLaunch}>
                Launch execution
              </button>
              <button className="btn btn-secondary btn-md" onClick={addComposerStage}>
                Add stage
              </button>
            </div>
            <div className="composer-list">
              {composerStages.map((stage, index) => {
                const tool = tools.find((item) => item.id === Number(stage.toolId));
                const toolsForStageType = getToolsForStageName(tools, serviceTypes, stage.stageName || stage.stageType);
                return (
                  <div className="composer-stage" key={stage.localId}>
                    <div className="composer-stage-top">
                      <div>
                        <div className="eyebrow">Stage {index + 1}</div>
                        <div className="pipeline-title">{tool?.name || "Select tool"}</div>
                      </div>
                      <button className="btn btn-destructive btn-sm" onClick={() => removeComposerStage(stage.localId)}>
                        Remove
                      </button>
                    </div>
                    <div className="two-column-layout compact">
                      <label className="field">
                        <span>Phase</span>
                        <select
                          value={stage.stageName || stage.stageType}
                          onChange={(event) => {
                            const nextStageName = event.target.value;
                            const nextTool = getToolsForStageName(tools, serviceTypes, nextStageName)[0];
                            updateComposerStage(stage.localId, {
                              stageType: nextStageName,
                              stageName: nextStageName,
                              toolId: nextTool?.id || "",
                              params: buildDefaultParams(nextTool, data?.projectFiles || []),
                            });
                          }}
                        >
                          {stageTypeOptions.map((option) => (
                            <option key={option.name} value={option.name}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className="field">
                        <span>Tool</span>
                        <select
                          value={stage.toolId}
                          onChange={(event) => {
                            const nextTool = tools.find((item) => item.id === Number(event.target.value));
                            updateComposerStage(stage.localId, {
                              toolId: Number(event.target.value),
                              stageType: stage.stageName || stage.stageType,
                              stageName: nextTool
                                ? resolveStageName(nextTool, serviceTypes)
                                : stage.stageName || stage.stageType,
                              params: buildDefaultParams(nextTool, data?.projectFiles || []),
                            });
                          }}
                        >
                          <option value="">Select tool</option>
                          {toolsForStageType.map((toolOption) => (
                            <option key={toolOption.id} value={toolOption.id}>
                              {toolOption.name}
                            </option>
                          ))}
                        </select>
                      </label>
                    </div>
                    <ParameterFormGenerator
                      tool={tool}
                      stageName={stage.stageName}
                      values={stage.params}
                      projectFiles={data?.projectFiles || []}
                      uploadState={uploadingField}
                      localId={stage.localId}
                      onUploadFile={handleUploadForStage}
                      onChange={(key, value) =>
                        updateComposerStage(stage.localId, {
                          params: { ...stage.params, [key]: normalizeFieldValue(value) },
                        })
                      }
                    />
                  </div>
                );
              })}
              {!composerStages.length ? <div className="empty-state">Start by adding a stage to compose a new execution.</div> : null}
            </div>
          </Panel>
        </div>
        <div className="stacked-panels">
          <Panel
            title="Execution detail"
            description="Live detail, outputs and failure context for the selected stage"
            actions={selectedStage ? <StatusBadge status={selectedStage.status} /> : null}
          >
            {selectedStage ? (
              <>
                <div className="detail-block">
                  <div className="eyebrow">Tool</div>
                  <div>{selectedStage.tool}</div>
                </div>

                <div className="detail-block">
                  <div className="eyebrow">Downloads</div>
                  <div className="pipeline-list">
                    {artifacts.map((artifact) => (
                      <button
                        key={artifact.path}
                        className="pipeline-list-item"
                        onClick={() => downloadStageArtifact(selectedStage.id, artifact.path)}
                      >
                        <div>
                          <div className="table-primary">{artifact.name}</div>
                          <div className="table-secondary">{formatBytes(artifact.size)}</div>
                        </div>
                        <span className="link-button">Download</span>
                      </button>
                    ))}
                    {!artifacts.length ? <div className="empty-state compact">No downloadable artifacts yet.</div> : null}
                  </div>
                </div>
                {selectedStage.status === "waiting_for_approval" ? (
                  <div className="detail-block approval-block">
                    <div className="eyebrow">Manual approval</div>
                    <div className="table-secondary">
                      Esta etapa quedo pausada esperando aprobacion manual. Puedes revisar y ajustar sus parametros antes de continuar.
                    </div>
                    <ParameterFormGenerator
                      tool={selectedStageTool}
                      stageName={selectedStage.stage_name}
                      values={selectedStageApprovalParams}
                      projectFiles={data?.projectFiles || []}
                      uploadState={uploadingField}
                      localId={`approval-${selectedStage.id}`}
                      onUploadFile={handleUploadForApproval}
                      onChange={(key, value) =>
                        setApprovalParamsByStage((current) => ({
                          ...current,
                          [selectedStage.id]: {
                            ...(current[selectedStage.id] || selectedStageApprovalParams),
                            [key]: normalizeFieldValue(value),
                          },
                        }))
                      }
                    />
                    <button className="btn btn-secondary btn-md" onClick={handleApprove}>
                      Approve next stage
                    </button>
                  </div>
                ) : null}
                <div className="detail-block">
                  <div className="eyebrow">Execution summary</div>
                  <div className="summary-list">
                    <div>Started: {selectedStage.started_at ? new Date(selectedStage.started_at).toLocaleString() : "n/a"}</div>
                    <div>Finished: {selectedStage.finished_at ? new Date(selectedStage.finished_at).toLocaleString() : "n/a"}</div>
                    <div>Retries: {selectedStage.retry_count}</div>
                    <div>Runtime image: {selectedStage.output_metadata?.image || "n/a"}</div>
                  </div>
                </div>
              </>
            ) : (
              <div className="empty-state">Select a stage to inspect it.</div>
            )}
          </Panel>

          <Panel title="Manual controls" description="Retry a stage with new params or resolve approval from the stage detail">
            <div className="form-stack">
              <div className="table-secondary">
                {approvalWaiting
                  ? "Selecciona la etapa en espera para aprobarla desde su panel de detalle."
                  : "Escoge una etapa completada o fallida para relanzarla con parametros ajustados."}
              </div>
              <label className="field">
                <span>Stage to retry</span>
                <select value={retryStageId} onChange={(event) => setRetryStageId(event.target.value)}>
                  {!retryableStages.length ? <option value="">No executed stages yet</option> : null}
                  {retryableStages.map((stage) => (
                    <option key={stage.id} value={stage.id}>
                      Stage {stage.stage_order_index + 1} - {stage.stage_name} - {stage.tool} - {stage.status}
                    </option>
                  ))}
                </select>
              </label>
              {selectedRetryStage ? (
                <ParameterFormGenerator
                  tool={retryStageTool}
                  stageName={selectedRetryStage.stage_name}
                  values={retryStageParams}
                  projectFiles={data?.projectFiles || []}
                  uploadState={uploadingField}
                  localId={`retry-${selectedRetryStage.id}`}
                  onUploadFile={handleUploadForRetry}
                  onChange={(key, value) =>
                    setRetryParamsByStage((current) => ({
                      ...current,
                      [selectedRetryStage.id]: {
                        ...(current[selectedRetryStage.id] || retryStageParams),
                        [key]: normalizeFieldValue(value),
                      },
                    }))
                  }
                />
              ) : null}
              <button className="btn btn-secondary btn-md" disabled={!selectedRetryStage} onClick={handleRetry}>Retry stage</button>
            </div>
          </Panel>
        </div>
      </div>
    </ProtectedLayout>
  );
}

function MyFilesPage({ user }) {
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [expandedOutputStages, setExpandedOutputStages] = useState({});
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  const { data, loading } = usePolling(async () => {
    const projects = await getProjects();
    const activeProjectId = selectedProjectId || projects[0]?.id || "";
    const [files, outputs] = activeProjectId
      ? await Promise.all([getProjectFiles(activeProjectId), getProjectOutputs(activeProjectId)])
      : [[], []];
    return { projects, files, outputs, activeProjectId };
  }, [selectedProjectId, refreshKey], 8000);

  useEffect(() => {
    if (!selectedProjectId && data?.activeProjectId) {
      setSelectedProjectId(String(data.activeProjectId));
    }
  }, [data?.activeProjectId, selectedProjectId]);

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file || !selectedProjectId) return;
    setError("");
    try {
      await uploadProjectFile(selectedProjectId, file, "shared_inputs");
      setRefreshKey((value) => value + 1);
    } catch (err) {
      setError(err.message || "No se pudo subir el archivo");
    } finally {
      event.target.value = "";
    }
  }

  function toggleOutputStage(stageExecutionId) {
    setExpandedOutputStages((current) => ({
      ...current,
      [stageExecutionId]: !current[stageExecutionId],
    }));
  }

  return (
    <ProtectedLayout
      title="My Files / Outputs"
      subtitle="Uploaded inputs and downloadable outputs for the selected project"
      user={user}
      actions={
        <div className="page-actions">
          <label className="btn btn-secondary btn-sm upload-button">
            Upload file
            <input type="file" hidden onChange={handleUpload} />
          </label>
        </div>
      }
    >
      {error ? <div className="error-box">{error}</div> : null}
      <div className="stacked-panels">
        <Panel title="Project scope" description="Choose which project files and outputs to inspect">
          <label className="field narrow-field">
            <span>Project</span>
            <select value={selectedProjectId} onChange={(event) => setSelectedProjectId(event.target.value)}>
              {(data?.projects || []).map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
        </Panel>

        <div className="dashboard-grid">
          <Panel title="Available outputs" description="Completed stage artifacts ready to download">
            {loading && !data ? <div className="empty-state">Loading outputs...</div> : null}
            <div className="output-groups">
              {(data?.outputs || []).map((entry) => {
                const isExpanded = expandedOutputStages[entry.stage_execution_id] ?? false;
                return (
                  <div key={`${entry.stage_execution_id}`} className="output-group">
                    <button
                      className="output-stage-toggle"
                      onClick={() => toggleOutputStage(entry.stage_execution_id)}
                    >
                      <div className="output-stage-toggle-main">
                        <span className="output-stage-caret">{isExpanded ? "v" : ">"}</span>
                        <div>
                          <div className="table-primary">Pipeline #{entry.pipeline_id} · Stage {entry.stage_order_index + 1}</div>
                          <div className="table-secondary">
                            {entry.stage_name} · {entry.artifacts.length} output{entry.artifacts.length === 1 ? "" : "s"}
                          </div>
                        </div>
                      </div>
                      <StatusBadge status={entry.status} />
                    </button>
                    {isExpanded ? (
                      <div className="output-icon-grid">
                        {entry.artifacts.map((artifact) => (
                          <button
                            key={artifact.path}
                            className="output-icon-card"
                            onClick={() => downloadStageArtifact(entry.stage_execution_id, artifact.path)}
                          >
                            <div className="output-icon-preview">{getArtifactGlyph(artifact.name)}</div>
                            <div className="output-icon-name">{artifact.name}</div>
                            <div className="table-secondary">{formatBytes(artifact.size)}</div>
                          </button>
                        ))}
                        {!entry.artifacts.length ? <div className="empty-state compact">No outputs in this stage.</div> : null}
                      </div>
                    ) : null}
                  </div>
                );
              })}
              {!data?.outputs?.length ? <div className="empty-state compact">No outputs available yet.</div> : null}
            </div>
          </Panel>

          <Panel title="Uploaded inputs" description="Files available to pipelines in this project">
            {loading && !data ? <div className="empty-state">Loading files...</div> : null}
            <div className="pipeline-list">
              {(data?.files || []).map((file) => (
                <button
                  key={file.relative_path}
                  className="pipeline-list-item"
                  onClick={() => downloadProjectFile(selectedProjectId, file.relative_path)}
                >
                  <div>
                    <div className="table-primary">{file.name}</div>
                    <div className="table-secondary">{file.relative_path}</div>
                  </div>
                  <div className="table-secondary">{formatBytes(file.size)}</div>
                </button>
              ))}
              {!data?.files?.length ? <div className="empty-state compact">No uploaded inputs yet.</div> : null}
            </div>
          </Panel>
        </div>
      </div>
    </ProtectedLayout>
  );
}

function DocumentationPage({ user }) {
  const { data, error, loading } = usePolling(async () => getDocumentationEntries(), [], 30000);

  return (
    <ProtectedLayout
      title="Documentation"
      subtitle="Project docs, user manual and technical references bundled with the platform"
      user={user}
    >
      {error ? <div className="error-box">{error}</div> : null}
      <div className="stacked-panels">
        <Panel title="Available documents" description="Core references served directly from the docs module">
          {loading && !data ? <div className="empty-state">Loading documentation...</div> : null}
          <div className="pipeline-list">
            {(data || []).map((entry) => (
              <a
                key={entry.name}
                className="pipeline-list-item"
                href={getDocumentationDownloadUrl(entry.name)}
                target="_blank"
                rel="noreferrer"
              >
                <div>
                  <div className="table-primary">{entry.title}</div>
                  <div className="table-secondary">{entry.description}</div>
                </div>
                <div className="documentation-meta">
                  <span className="status-badge status-pending"><span className="bdot"></span>{entry.category}</span>
                  <span className="link-button">{formatBytes(entry.size)}</span>
                </div>
              </a>
            ))}
            {!data?.length ? <div className="empty-state compact">No documentation entries available.</div> : null}
          </div>
        </Panel>
      </div>
    </ProtectedLayout>
  );
}

function ReportsPage({ user }) {
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [selectedPipelineId, setSelectedPipelineId] = useState("");
  const [error, setError] = useState("");

  const { data, loading } = usePolling(async () => {
    const projects = await getProjects();
    const activeProjectId = selectedProjectId || projects[0]?.id || "";
    const pipelines = activeProjectId ? await getPipelines(activeProjectId) : [];
    const activePipelineId = selectedPipelineId || pipelines[0]?.id || "";
    const [projectOverview, pipelineOverview] = await Promise.all([
      activeProjectId ? getProjectReportsOverview(activeProjectId) : null,
      activeProjectId && activePipelineId ? getPipelineReportOverview(activeProjectId, activePipelineId) : null,
    ]);
    return {
      projects,
      pipelines,
      activeProjectId,
      activePipelineId,
      projectOverview,
      pipelineOverview,
    };
  }, [selectedProjectId, selectedPipelineId], 12000);

  useEffect(() => {
    if (!selectedProjectId && data?.activeProjectId) {
      setSelectedProjectId(String(data.activeProjectId));
    }
  }, [data?.activeProjectId, selectedProjectId]);

  useEffect(() => {
    if (!selectedPipelineId && data?.activePipelineId) {
      setSelectedPipelineId(String(data.activePipelineId));
    }
  }, [data?.activePipelineId, selectedPipelineId]);

  async function handleProjectDownload(format) {
    if (!selectedProjectId) return;
    setError("");
    try {
      await downloadProjectReport(selectedProjectId, format);
    } catch (err) {
      setError(err.message || "No se pudo descargar el reporte del proyecto");
    }
  }

  async function handlePipelineDownload(format) {
    if (!selectedProjectId || !selectedPipelineId) return;
    setError("");
    try {
      await downloadPipelineReport(selectedProjectId, selectedPipelineId, format);
    } catch (err) {
      setError(err.message || "No se pudo descargar el reporte del pipeline");
    }
  }

  return (
    <ProtectedLayout
      title="Reports"
      subtitle="Comparative analytics, scientific summaries and downloadable reports for projects and pipelines"
      user={user}
    >
      {error ? <div className="error-box">{error}</div> : null}
      <div className="stacked-panels">
        <Panel title="Report scope" description="Select the project and pipeline you want to inspect or export">
          <div className="two-column-layout compact">
            <label className="field">
              <span>Project</span>
              <select value={selectedProjectId} onChange={(event) => setSelectedProjectId(event.target.value)}>
                {(data?.projects || []).map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Pipeline</span>
              <select value={selectedPipelineId} onChange={(event) => setSelectedPipelineId(event.target.value)}>
                {(data?.pipelines || []).map((pipeline) => (
                  <option key={pipeline.id} value={pipeline.id}>
                    Pipeline #{pipeline.id}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </Panel>

        <div className="dashboard-grid">
          <Panel
            title="Project report"
            description="Cross-pipeline summary for the selected project"
            actions={
              <div className="page-actions">
                <button className="btn btn-secondary btn-sm" disabled={!selectedProjectId} onClick={() => handleProjectDownload("md")}>
                  Download MD
                </button>
                <button className="btn btn-secondary btn-sm" disabled={!selectedProjectId} onClick={() => handleProjectDownload("json")}>
                  Download JSON
                </button>
              </div>
            }
          >
            {loading && !data ? <div className="empty-state">Loading reports...</div> : null}
            {data?.projectOverview ? (
              <div className="summary-list">
                <div>Project: {data.projectOverview.project_name}</div>
                <div>Pipelines: {data.projectOverview.kpis.pipelines}</div>
                <div>Completed: {data.projectOverview.kpis.completed_pipelines}</div>
                <div>Failed: {data.projectOverview.kpis.failed_pipelines}</div>
                <div>Artifacts: {data.projectOverview.kpis.artifacts}</div>
                <div>Total output size: {formatBytes(data.projectOverview.kpis.total_output_size_bytes)}</div>
              </div>
            ) : (
              <div className="empty-state compact">No project report available yet.</div>
            )}
          </Panel>

          <Panel
            title="Pipeline report"
            description="Detailed stage report for the selected pipeline"
            actions={
              <div className="page-actions">
                <button
                  className="btn btn-secondary btn-sm"
                  disabled={!selectedProjectId || !selectedPipelineId}
                  onClick={() => handlePipelineDownload("md")}
                >
                  Download MD
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  disabled={!selectedProjectId || !selectedPipelineId}
                  onClick={() => handlePipelineDownload("json")}
                >
                  Download JSON
                </button>
              </div>
            }
          >
            {data?.pipelineOverview ? (
              <div className="summary-list">
                <div>Status: {data.pipelineOverview.status}</div>
                <div>Version: {data.pipelineOverview.version || "n/a"}</div>
                <div>Completed stages: {data.pipelineOverview.kpis.completed_stages}/{data.pipelineOverview.kpis.total_stages}</div>
                <div>Artifacts: {data.pipelineOverview.kpis.artifact_count}</div>
                <div>Duration: {formatSeconds(data.pipelineOverview.kpis.duration_seconds)}</div>
                <div>Total output size: {formatBytes(data.pipelineOverview.kpis.total_output_size_bytes)}</div>
              </div>
            ) : (
              <div className="empty-state compact">No pipeline report available yet.</div>
            )}
          </Panel>
        </div>

        <div className="dashboard-grid">
          <Panel title="Cross-pipeline comparison" description="Compare scientific and operational signals between pipelines in the same project">
            {data?.projectOverview?.comparison?.ranked_pipelines?.length ? (
              <div className="comparison-table">
                {data.projectOverview.comparison.ranked_pipelines.map((pipeline) => (
                  <div key={pipeline.pipeline_id} className="comparison-row">
                    <div>
                      <div className="table-primary">Pipeline #{pipeline.pipeline_id}</div>
                      <div className="table-secondary">{pipeline.version || "n/a"}</div>
                    </div>
                    <div className="comparison-metrics">
                      <span>{formatSeconds(pipeline.duration_seconds)}</span>
                      <span>{pipeline.artifact_count} artifacts</span>
                      <span>{formatBytes(pipeline.output_size_bytes)}</span>
                      <span>TM {formatMetricValue(pipeline.docking_tm_score_best)}</span>
                      <span>E {formatMetricValue(pipeline.docking_energy_min)}</span>
                    </div>
                    <StatusBadge status={pipeline.status} />
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state compact">Need at least one completed pipeline to compare.</div>
            )}
          </Panel>

          <Panel title="Scientific highlights" description="Best current signals extracted from generated artifacts">
            {data?.projectOverview?.comparison?.highlights ? (
              <div className="summary-list">
                <div>Fastest pipeline: {formatPipelineLabel(data.projectOverview.comparison.highlights.fastest_pipeline_id)}</div>
                <div>Largest output set: {formatPipelineLabel(data.projectOverview.comparison.highlights.largest_output_pipeline_id)}</div>
                <div>Best docking energy: {formatPipelineLabel(data.projectOverview.comparison.highlights.best_energy_pipeline_id)}</div>
                <div>Best TM-score: {formatPipelineLabel(data.projectOverview.comparison.highlights.best_tm_score_pipeline_id)}</div>
              </div>
            ) : (
              <div className="empty-state compact">No scientific highlights yet.</div>
            )}
          </Panel>
        </div>

        <div className="dashboard-grid">
          <Panel title="Visualization: Project comparison" description="Chart-ready data rendered directly from report outputs">
            <MiniBarChart
              title="Pipeline duration"
              unit="s"
              points={data?.projectOverview?.visualizations?.pipeline_duration_seconds || []}
            />
            <MiniBarChart
              title="Pipeline TM-score"
              unit=""
              points={data?.projectOverview?.visualizations?.pipeline_tm_score || []}
            />
            <MiniBarChart
              title="Pipeline output size"
              unit="bytes"
              points={data?.projectOverview?.visualizations?.pipeline_output_size_bytes || []}
              formatter={formatBytes}
            />
          </Panel>

          <Panel title="Visualization: Stage progression" description="Per-stage scientific and runtime trends for the selected pipeline">
            <MiniBarChart
              title="Stage duration"
              unit="s"
              points={data?.pipelineOverview?.visualizations?.stage_duration_seconds || []}
            />
            <MiniBarChart
              title="Atom count"
              unit=""
              points={data?.pipelineOverview?.visualizations?.stage_atom_count || []}
            />
            <MiniBarChart
              title="Energy"
              unit=""
              points={data?.pipelineOverview?.visualizations?.stage_energy || []}
            />
          </Panel>
        </div>

        <Panel title="Stage summary" description="Latest stage results included in the selected pipeline report">
          <div className="pipeline-list">
            {(data?.pipelineOverview?.stages || []).map((stage) => (
              <div key={stage.id} className="pipeline-list-item report-stage-item">
                <div>
                  <div className="table-primary">Stage {stage.stage_order_index + 1}: {stage.stage_name}</div>
                  <div className="table-secondary">{stage.tool}</div>
                  <div className="table-secondary">
                    {formatSeconds(stage.duration_seconds)} · {formatBytes(stage.output_size_bytes)}
                  </div>
                </div>
                <div className="documentation-meta">
                  <span className="table-secondary">{stage.artifact_count} artifacts</span>
                  <StatusBadge status={stage.status} />
                </div>
                <ScientificMetricList metrics={stage.scientific_metrics} />
              </div>
            ))}
            {!data?.pipelineOverview?.stages?.length ? <div className="empty-state compact">No stages to report yet.</div> : null}
          </div>
        </Panel>
      </div>
    </ProtectedLayout>
  );
}

function ToolsPage({ user }) {
  const { data, error, loading } = usePolling(async () => {
    const [tools, serviceTypes] = await Promise.all([getTools(), getServiceTypes()]);
    return { tools, serviceTypes };
  }, [], 15000);

  function serviceTypeName(serviceTypeId) {
    return data?.serviceTypes?.find((type) => type.id === serviceTypeId)?.name || `service_type_${serviceTypeId}`;
  }

  return (
    <ProtectedLayout
      title="Tools explorer"
      subtitle="Imported tools, runtimes and parameter contracts loaded from XML"
      user={user}
    >
      {error ? <div className="error-box">{error}</div> : null}
      {loading && !data ? <div className="empty-state">Loading tools...</div> : null}
      <div className="tool-grid">
        {(data?.tools || []).map((tool) => (
          <Panel
            key={tool.id}
            title={tool.name}
            description={`${serviceTypeName(tool.service_type_id)} - ${tool.version || "no version"}`}
          >
            <div className="detail-block">
              <div className="eyebrow">Description</div>
              <div>{tool.description || "No description."}</div>
            </div>
            <div className="detail-block">
              <div className="eyebrow">Runtime</div>
              <code>{tool.runtime?.mode || "n/a"} - {tool.runtime?.image || "n/a"}</code>
            </div>
            <div className="detail-block">
              <div className="eyebrow">Parameters</div>
              <div className="parameter-chip-list">
                {(tool.parameters || []).filter((parameter) => parameter.name !== "output_dir").map((parameter) => (
                  <span className="parameter-chip" key={parameter.id}>
                    {parameter.name} - {parameter.data_type}
                  </span>
                ))}
              </div>
            </div>
          </Panel>
        ))}
      </div>
    </ProtectedLayout>
  );
}

function MonitoringPage({ user }) {
  const { data, error, loading } = usePolling(
    async () => {
      const [summary, tools] = await Promise.all([getMonitoringSummary(), getTools()]);
      return { ...summary, tools };
    },
    [],
    5000
  );

  return (
    <ProtectedLayout
      title="Monitoring"
      subtitle="System health and available stage tools"
      user={user}
    >
      {error ? <div className="error-box">{error}</div> : null}
      {loading && !data ? <div className="empty-state">Loading monitoring...</div> : null}
      <div className="stacked-panels">
        <Panel title="Available stage tools" description="Imported tools that can be used in execution stages">
          <ToolsPanel tools={data?.tools || []} />
        </Panel>
        <Panel title="Active pipelines">
          <div className="card-grid">
            {(data?.pipelines || []).map((pipeline) => (
              <PipelineCard key={pipeline.pipeline_id} pipeline={pipeline} />
            ))}
          </div>
        </Panel>
      </div>
    </ProtectedLayout>
  );
}

function AboutPage({ user }) {
  const userGuideUrl = getUserGuideUrl();
  return (
    <ProtectedLayout
      title="About Us"
      subtitle="General information about the platform and its user workflow"
      user={user}
    >
      <div className="stacked-panels">
        <Panel title="Platform overview" description="What this application is built to do">
          <div className="summary-list">
            <div>This console orchestrates staged bioinformatics workflows for refinement, docking, and evolutionary optimization.</div>
            <div>Users work with uploaded project files, monitor execution state, and download generated artifacts without touching internal storage paths.</div>
            <div>The current architecture combines a React frontend, FastAPI backend, Celery workers, Dockerized scientific runtimes, and persistent shared storage.</div>
          </div>
        </Panel>
        <Panel title="Workflow principles" description="What the user can expect from the product">
          <div className="summary-list">
            <div>Inputs are uploaded to a project workspace from the web interface.</div>
            <div>Output directories are assigned automatically by the platform for each user, pipeline, and stage.</div>
            <div>Completed outputs can be downloaded from the global files view and from execution results.</div>
          </div>
        </Panel>
      </div>
    </ProtectedLayout>
  );
}

export function App() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  async function loadUser() {
    if (!isAuthenticated()) {
      setUser(null);
      setReady(true);
      return;
    }
    try {
      const me = await getMe();
      setUser(me);
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setReady(true);
    }
  }

  useEffect(() => {
    loadUser();
  }, []);

  useEffect(() => {
    if (ready && !user && !["/login", "/register"].includes(window.location.pathname)) {
      navigate("/login");
    }
  }, [ready, user, navigate]);

  if (!ready) {
    return <div className="login-page"><div className="empty-state">Booting console...</div></div>;
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage onAuthenticated={loadUser} />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<DashboardPage user={user} />} />
      <Route path="/profile" element={<ProfilePage user={user} />} />
      <Route path="/projects" element={<ProjectsPage user={user} />} />
      <Route path="/files" element={<MyFilesPage user={user} />} />
      <Route path="/reports" element={<ReportsPage user={user} />} />
      <Route path="/documentation" element={<DocumentationPage user={user} />} />
      <Route path="/projects/:projectId/pipelines/:pipelineId" element={<PipelineDetailPage user={user} />} />
      <Route path="/tools" element={<ToolsPage user={user} />} />
      <Route path="/monitoring" element={user?.role === "admin" ? <MonitoringPage user={user} /> : <Navigate to="/" replace />} />
      <Route path="/about" element={<AboutPage user={user} />} />
      <Route path="/login" element={<Navigate to="/" replace />} />
      <Route path="/register" element={<Navigate to="/" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// ============ Funciones auxiliares ============

function resolveStageName(tool, serviceTypes) {
  if (!tool) return "refinement";
  const serviceType = serviceTypes.find((item) => item.id === tool.service_type_id);
  return serviceType?.name || "refinement";
}

function buildDefaultParams(tool, projectFiles = []) {
  const params = {};
  for (const parameter of tool?.parameters || []) {
    if (parameter.is_output || parameter.name === "output_dir") continue;
    if (parameter.data_type === "bool") {
      params[parameter.name] = String(parameter.default_value).toLowerCase() === "true";
    } else if (parameter.default_value !== null && parameter.default_value !== undefined && parameter.default_value !== "") {
      params[parameter.name] = parameter.default_value;
    } else if (parameter.data_type === "file" || parameter.data_type === "directory") {
      params[parameter.name] = pickDefaultProjectPath(parameter, projectFiles);
    } else if (parameter.default_value !== null && parameter.default_value !== undefined) {
      params[parameter.name] = parameter.default_value;
    } else {
      params[parameter.name] = "";
    }
  }
  return params;
}

function normalizeFieldValue(value) {
  return value;
}

function getStageTypeOptions(serviceTypes, tools) {
  const knownOrder = ["refinement", "docking", "evolution"];
  const discovered = new Set(
    tools
      .map((tool) => serviceTypes.find((item) => item.id === tool.service_type_id)?.name)
      .filter(Boolean),
  );
  const ordered = [
    ...knownOrder.filter((name) => discovered.has(name)),
    ...Array.from(discovered).filter((name) => !knownOrder.includes(name)),
  ];
  return ordered.map((name) => ({
    name,
    label: name.charAt(0).toUpperCase() + name.slice(1),
  }));
}

function getToolsForStageName(tools, serviceTypes, stageName) {
  return tools.filter((tool) => resolveStageName(tool, serviceTypes) === stageName);
}

function pickDefaultProjectPath(parameter, projectFiles) {
  const matches = (projectFiles || []).filter((file) => matchesProjectPathParameter(file, parameter));
  return matches[0]?.absolute_path || "";
}

function matchesProjectPathParameter(file, parameter) {
  const format = (parameter.format || "").toLowerCase();
  if (parameter.data_type === "directory") {
    return file.name.toLowerCase().endsWith(".zip");
  }
  if (!format) return true;
  return file.name.toLowerCase().endsWith(`.${format}`);
}

function isAutoResolvedParameter(stageName, parameterName) {
  const hiddenByStage = {
    docking: ["receptor_path", "ligand_path", "receptor_id", "ligand_id"],
    evolution: ["scenario_path", "input_scenario_path", "scenario_dir", "complex_pdb_path"],
  };
  return (hiddenByStage[stageName] || []).includes(parameterName);
}

function getArtifactGlyph(fileName) {
  const extension = (fileName?.split(".").pop() || "").toLowerCase();
  if (["pdb", "pdbqt", "mol2", "sdf"].includes(extension)) return extension.toUpperCase();
  if (["zip", "tar", "gz"].includes(extension)) return "ZIP";
  if (["json"].includes(extension)) return "JSON";
  if (["csv", "tsv", "sc"].includes(extension)) return "TAB";
  if (["txt", "log", "md"].includes(extension)) return "TXT";
  return extension ? extension.slice(0, 4).toUpperCase() : "FILE";
}

function formatBytes(value) {
  if (!Number.isFinite(value)) return "n/a";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatSeconds(value) {
  if (!Number.isFinite(value)) return "n/a";
  if (value < 60) return `${value.toFixed(1)} s`;
  return `${(value / 60).toFixed(1)} min`;
}

function formatMetricValue(value) {
  if (!Number.isFinite(value)) return "n/a";
  return value.toFixed(3);
}

function formatPipelineLabel(pipelineId) {
  return pipelineId ? `Pipeline #${pipelineId}` : "n/a";
}

function MiniBarChart({ title, points, formatter, unit }) {
  const numericPoints = (points || []).filter((point) => Number.isFinite(point.value));
  const maxValue = numericPoints.length ? Math.max(...numericPoints.map((point) => Math.abs(point.value))) : 0;

  return (
    <div className="chart-block">
      <div className="eyebrow">{title}</div>
      <div className="chart-stack">
        {numericPoints.length ? numericPoints.map((point) => {
          const width = maxValue ? Math.max((Math.abs(point.value) / maxValue) * 100, 4) : 0;
          const label = formatter
            ? formatter(point.value)
            : unit === "s"
              ? formatSeconds(point.value)
              : formatMetricValue(point.value);
          return (
            <div key={point.label} className="chart-row">
              <div className="chart-label">{point.label}</div>
              <div className="chart-bar-track">
                <div className="chart-bar-fill" style={{ width: `${width}%` }} />
              </div>
              <div className="chart-value">{label}</div>
            </div>
          );
        }) : <div className="empty-state compact">No visualization data yet.</div>}
      </div>
    </div>
  );
}

function ScientificMetricList({ metrics }) {
  const entries = Object.entries(metrics || {}).filter(([, value]) => Number.isFinite(value));
  if (!entries.length) {
    return <div className="table-secondary">No scientific metrics extracted.</div>;
  }

  return (
    <div className="scientific-metric-list">
      {entries.map(([key, value]) => (
        <span key={key} className="parameter-chip">
          {key}: {Number.isInteger(value) ? value : value.toFixed(3)}
        </span>
      ))}
    </div>
  );
}