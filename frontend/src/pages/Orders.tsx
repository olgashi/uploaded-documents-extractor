import { useEffect, useState } from "react";
import { listOrders, deleteOrder, updateOrder } from "../api/client";
import type { Order } from "../api/client";

interface Props {
  refresh: number;
}

const STATUS_LABEL: Record<string, string> = {
  pending: "Pending",
  processing: "Processing",
  completed: "Completed",
  cancelled: "Cancelled",
};

const STATUS_OPTIONS = ["pending", "processing", "completed", "cancelled"];

interface OrderDraft {
  patient_first_name: string;
  patient_last_name: string;
  patient_dob: string;
  status: string;
  notes: string;
}

export default function Orders({ refresh }: Props) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<OrderDraft | null>(null);
  const [saving, setSaving] = useState(false);
  const PAGE_SIZE = 10;

  useEffect(() => {
    setLoading(true);
    setError("");
    listOrders(page, PAGE_SIZE)
      .then((data) => {
        setOrders(data.items);
        setTotal(data.total);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [page, refresh]);

  async function handleDelete(id: string) {
    if (!confirm("Delete this order?")) return;
    try {
      await deleteOrder(id);
      setOrders((prev) => prev.filter((o) => o.id !== id));
      setTotal((t) => t - 1);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Delete failed");
    }
  }

  function startEdit(order: Order) {
    setEditingId(order.id);
    setDraft({
      patient_first_name: order.patient_first_name,
      patient_last_name: order.patient_last_name,
      patient_dob: order.patient_dob,
      status: order.status,
      notes: order.notes ?? "",
    });
  }

  function cancelEdit() {
    setEditingId(null);
    setDraft(null);
  }

  async function saveEdit(id: string) {
    if (!draft) return;
    setSaving(true);
    try {
      const updated = await updateOrder(id, {
        patient_first_name: draft.patient_first_name,
        patient_last_name: draft.patient_last_name,
        patient_dob: draft.patient_dob,
        status: draft.status,
        notes: draft.notes,
      });
      setOrders((prev) => prev.map((order) => (order.id === id ? updated : order)));
      cancelEdit();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Update failed");
    } finally {
      setSaving(false);
    }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  if (loading) return <p className="loading">Loading orders…</p>;
  if (error) return <p className="error">{error}</p>;

  return (
    <div className="orders-page">
      <h2>Orders ({total})</h2>
      {orders.length === 0 ? (
        <p className="empty">No orders yet. Upload a document to create one.</p>
      ) : (
        <>
          <table className="orders-table">
            <thead>
              <tr>
                <th>Patient</th>
                <th>DOB</th>
                <th>Status</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  {editingId === o.id && draft ? (
                    <>
                      <td>
                        <div className="edit-grid">
                          <input
                            value={draft.patient_first_name}
                            onChange={(e) => setDraft({ ...draft, patient_first_name: e.target.value })}
                            aria-label="First name"
                          />
                          <input
                            value={draft.patient_last_name}
                            onChange={(e) => setDraft({ ...draft, patient_last_name: e.target.value })}
                            aria-label="Last name"
                          />
                        </div>
                      </td>
                      <td>
                        <input
                          type="date"
                          value={draft.patient_dob}
                          onChange={(e) => setDraft({ ...draft, patient_dob: e.target.value })}
                          aria-label="Date of birth"
                        />
                      </td>
                      <td>
                        <select
                          value={draft.status}
                          onChange={(e) => setDraft({ ...draft, status: e.target.value })}
                          aria-label="Status"
                        >
                          {STATUS_OPTIONS.map((status) => (
                            <option key={status} value={status}>
                              {STATUS_LABEL[status]}
                            </option>
                          ))}
                        </select>
                      </td>
                    </>
                  ) : (
                    <>
                      <td>{o.patient_first_name} {o.patient_last_name}</td>
                      <td>{o.patient_dob}</td>
                      <td><span className={`badge badge-${o.status}`}>{STATUS_LABEL[o.status] ?? o.status}</span></td>
                    </>
                  )}
                  <td>{new Date(o.created_at).toLocaleDateString()}</td>
                  <td>
                    {editingId === o.id ? (
                      <div className="row-actions">
                        <button
                          onClick={() => saveEdit(o.id)}
                          disabled={saving}
                          className="btn-secondary"
                        >
                          Save
                        </button>
                        <button onClick={cancelEdit} className="btn-secondary">
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div className="row-actions">
                        <button
                          onClick={() => startEdit(o)}
                          className="btn-secondary"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(o.id)}
                          className="btn-danger"
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {totalPages > 1 && (
            <div className="pagination">
              <button onClick={() => setPage((p) => p - 1)} disabled={page === 1}>
                ← Prev
              </button>
              <span>Page {page} of {totalPages}</span>
              <button onClick={() => setPage((p) => p + 1)} disabled={page === totalPages}>
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
