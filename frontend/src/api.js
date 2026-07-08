import { clearToken, getToken } from "./auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getToken();

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = "Error desconocido";

    try {
      const data = await response.json();
      message = extractApiDetail(data.detail) || message;
    } catch {
      const text = await response.text();
      message = text || message;
    }
    message = cleanErrorMessage(message);

    if (response.status === 401) {
      clearToken();
      throw new Error(message || "Credenciales incorrectas");
    }

    if (response.status === 403) {
      throw new Error(message || "Usuario no autorizado");
    }

    if (response.status === 404) {
      throw new Error(message || "Usuario no registrado");
    }

    throw new Error(message || `Error ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

async function binaryRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getToken();

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearToken();
    throw new Error("Tu sesion expiro. Vuelve a iniciar sesion.");
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(cleanErrorMessage(text || `Request failed with status ${response.status}`));
  }

  return response.blob();
}

function extractApiDetail(detail) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message || item?.detail || String(item))
      .filter(Boolean)
      .join("; ");
  }
  if (typeof detail === "object") {
    return detail.message || detail.error || detail.detail || JSON.stringify(detail);
  }
  return String(detail);
}

export function cleanErrorMessage(rawMessage) {
  if (!rawMessage) return "Error desconocido";

  let message = String(rawMessage)
    .replace(/\r/g, "\n")
    .replace(/\\n/g, "\n")
    .replace(/\\"/g, '"')
    .trim();

  const meaningfulPatterns = [
    /(?:SyntaxError|Syntax error):\s*[^\n]+/gi,
    /(?:ValueError|FileNotFoundError|RuntimeError|PermissionError|TimeoutError|KeyError|TypeError):\s*[^\n]+/gi,
    /(?:No such file or directory|No \.pdb file found|PDB source does not exist|Docker execution failed|Soft time limit exceeded)[^\n]*/gi,
    /(?:error|fatal):\s*[^\n]+/gi,
  ];

  for (const pattern of meaningfulPatterns) {
    const matches = [...message.matchAll(pattern)].map((match) => match[0].trim());
    if (matches.length) {
      return truncateError(cleanErrorPrefix(matches[matches.length - 1]));
    }
  }

  const usefulLines = message
    .split("\n")
    .map((line) => line.trim())
    .filter((line) =>
      line &&
      !line.startsWith("Traceback ") &&
      !line.startsWith("File ") &&
      !line.startsWith("at ") &&
      !line.includes("site-packages") &&
      !line.includes("/usr/local/lib/") &&
      !line.includes("node_modules"),
    );

  const selected = usefulLines[usefulLines.length - 1] || message.split("\n").find((line) => line.trim()) || message;
  return truncateError(cleanErrorPrefix(selected));
}

function cleanErrorPrefix(message) {
  return message
    .replace(/^stderr:\s*/i, "")
    .replace(/^detail:\s*/i, "")
    .replace(/^Exception:\s*/i, "")
    .trim();
}

function truncateError(message) {
  const normalized = message.replace(/\s+/g, " ").trim();
  if (normalized.length <= 220) return normalized;
  return `${normalized.slice(0, 217)}...`;
}

export async function login(email, password) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  return request("/auth/login", {
    method: "POST",
    body,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
}

export function register(payload) {
  return request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getMe() {
  return request("/auth/me");
}

export function getProfile() {
  return request("/profile");
}

export function updateProfile(payload) {
  return request("/profile", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function uploadAvatar(file) {
  const formData = new FormData();
  formData.append("avatar", file);
  return request("/profile/avatar", {
    method: "POST",
    body: formData,
  });
}

export function deactivateProfile() {
  return request("/profile", {
    method: "DELETE",
  });
}

export function getGroups() {
  return request("/groups");
}

export function createGroup(payload) {
  return request("/groups", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function addGroupMember(groupId, payload) {
  return request(`/groups/${groupId}/members`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateGroupMember(groupId, userId, payload) {
  return request(`/groups/${groupId}/members/${userId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function removeGroupMember(groupId, userId) {
  return request(`/groups/${groupId}/members/${userId}`, {
    method: "DELETE",
  });
}

export function getAssetUrl(path) {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_BASE_URL}${path}`;
}

export function getMonitoringSummary() {
  return request("/monitoring/summary");
}

export function getProjects() {
  return request("/projects/");
}

export function createProject(payload) {
  return request("/projects/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getPipelines(projectId) {
  return request(`/projects/${projectId}/pipelines/`);
}

export function createPipeline(projectId, payload) {
  return request(`/projects/${projectId}/pipelines/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getPipeline(projectId, pipelineId) {
  return request(`/projects/${projectId}/pipelines/${pipelineId}`);
}

export function deletePipeline(projectId, pipelineId) {
  return request(`/projects/${projectId}/pipelines/${pipelineId}`, {
    method: "DELETE",
  });
}

export function getProjectFiles(projectId) {
  return request(`/projects/${projectId}/files`);
}

export function getProjectOutputs(projectId) {
  return request(`/projects/${projectId}/outputs`);
}

export function getProjectReportsOverview(projectId) {
  return request(`/projects/${projectId}/reports/overview`);
}

export function getPipelineReportOverview(projectId, pipelineId) {
  return request(`/projects/${projectId}/pipelines/${pipelineId}/reports/overview`);
}

export async function downloadProjectReport(projectId, format = "md") {
  const blob = await binaryRequest(`/projects/${projectId}/reports/download?format=${encodeURIComponent(format)}`);
  triggerDownload(blob, `project_${projectId}_report.${format}`);
}

export async function downloadPipelineReport(projectId, pipelineId, format = "md") {
  const blob = await binaryRequest(
    `/projects/${projectId}/pipelines/${pipelineId}/reports/download?format=${encodeURIComponent(format)}`,
  );
  triggerDownload(blob, `pipeline_${pipelineId}_report.${format}`);
}

export async function uploadProjectFile(projectId, file, targetSubdir = "") {
  const formData = new FormData();
  formData.append("upload", file);
  const query = targetSubdir ? `?target_subdir=${encodeURIComponent(targetSubdir)}` : "";

  return request(`/projects/${projectId}/files/upload${query}`, {
    method: "POST",
    body: formData,
  });
}

export async function downloadProjectFile(projectId, relativePath) {
  const blob = await binaryRequest(
    `/projects/${projectId}/files/download?path=${encodeURIComponent(relativePath)}`,
  );
  triggerDownload(blob, relativePath.split("/").pop() || "download");
}

export function getUserGuideUrl() {
  return `${API_BASE_URL}/manual/user-guide`;
}

export function getDocumentationEntries() {
  return request("/documentation/entries");
}

export function getDocumentationDownloadUrl(name) {
  return `${API_BASE_URL}/documentation/download?name=${encodeURIComponent(name)}`;
}

export function getExecution(pipelineId) {
  return request(`/executions/${pipelineId}`);
}

export function getExecutionStages(pipelineId) {
  return request(`/executions/${pipelineId}/stages`);
}

export function getStageArtifacts(stageExecutionId) {
  return request(`/executions/stages/${stageExecutionId}/artifacts`);
}

export async function downloadStageArtifact(stageExecutionId, artifactPath) {
  const blob = await binaryRequest(
    `/executions/stages/${stageExecutionId}/artifacts/download?path=${encodeURIComponent(artifactPath)}`,
  );
  triggerDownload(blob, artifactPath.split(/[\\/]/).pop() || "artifact");
}

export function runPipeline(projectId, pipelineId, payload) {
  return request(`/projects/${projectId}/pipelines/${pipelineId}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function retryStage(pipelineId, payload) {
  return request(`/executions/${pipelineId}/retry-stage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function approvePipeline(pipelineId, payload = {}) {
  return request(`/executions/${pipelineId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getTools() {
  return request("/tools/");
}

export function getServiceTypes() {
  return request("/service-types/");
}

function triggerDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.URL.revokeObjectURL(url);
}
