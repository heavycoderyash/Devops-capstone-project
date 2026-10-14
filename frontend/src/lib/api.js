// All calls are relative: Nginx (Docker) or the Ingress (Kubernetes) routes /api to FastAPI.
const BASE = '/api';

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (response.status === 204) return null;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(describeError(body) || `Request failed (${response.status})`);
  }
  return body;
}

// FastAPI returns either {detail: "msg"} or {detail: [{loc, msg}, ...]} for validation errors.
export function describeError(body) {
  const { detail } = body ?? {};
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => `${d.loc?.at(-1) ?? 'field'}: ${d.msg}`).join('; ');
  }
  return '';
}

export const api = {
  listDoctors: () => request('/doctors'),
  createDoctor: (data) => request('/doctors', { method: 'POST', body: JSON.stringify(data) }),
  deleteDoctor: (id) => request(`/doctors/${id}`, { method: 'DELETE' }),

  listAppointments: (params = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    return request(`/appointments${query ? `?${query}` : ''}`);
  },
  stats: () => request('/appointments/stats'),
  bookAppointment: (data) => request('/appointments', { method: 'POST', body: JSON.stringify(data) }),
  updateAppointment: (id, data) => request(`/appointments/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAppointment: (id) => request(`/appointments/${id}`, { method: 'DELETE' }),
};
