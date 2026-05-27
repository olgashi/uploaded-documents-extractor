const BASE = "/api/v1";

function getToken(): string | null {
  return localStorage.getItem("token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export async function login(email: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${BASE}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });
  if (!res.ok) throw new Error("Invalid credentials");
  const data = await res.json();
  return data.access_token;
}

export interface Order {
  id: string;
  patient_first_name: string;
  patient_last_name: string;
  patient_dob: string;
  status: string;
  document_filename: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface OrderListResponse {
  items: Order[];
  total: number;
  page: number;
  page_size: number;
}

export interface OrderCreate {
  patient_first_name: string;
  patient_last_name: string;
  patient_dob: string;
  document_filename?: string;
  status?: string;
  notes?: string;
}

export type OrderUpdate = Partial<OrderCreate>;

export interface ExtractionResult {
  first_name: string;
  last_name: string;
  date_of_birth: string;
}

export async function listOrders(page = 1, pageSize = 20): Promise<OrderListResponse> {
  return request(`/orders?page=${page}&page_size=${pageSize}`);
}

export async function createOrder(data: OrderCreate): Promise<Order> {
  return request("/orders", { method: "POST", body: JSON.stringify(data) });
}

export async function updateOrder(id: string, data: OrderUpdate): Promise<Order> {
  return request(`/orders/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function deleteOrder(id: string): Promise<void> {
  return request(`/orders/${id}`, { method: "DELETE" });
}

export async function extractDocument(
  file: File
): Promise<{ extraction: ExtractionResult; filename: string }> {
  const form = new FormData();
  form.append("file", file);
  return request("/documents/extract", { method: "POST", body: form });
}

export async function uploadDocumentOrder(file: File): Promise<Order> {
  const form = new FormData();
  form.append("file", file);
  return request("/documents/upload-order", { method: "POST", body: form });
}
