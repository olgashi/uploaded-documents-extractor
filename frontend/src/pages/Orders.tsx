import { useEffect, useState } from "react";
import { listOrders, deleteOrder } from "../api/client";
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

export default function Orders({ refresh }: Props) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
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
                  <td>{o.patient_first_name} {o.patient_last_name}</td>
                  <td>{o.patient_dob}</td>
                  <td><span className={`badge badge-${o.status}`}>{STATUS_LABEL[o.status] ?? o.status}</span></td>
                  <td>{new Date(o.created_at).toLocaleDateString()}</td>
                  <td>
                    <button
                      onClick={() => handleDelete(o.id)}
                      className="btn-danger"
                    >
                      Delete
                    </button>
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
