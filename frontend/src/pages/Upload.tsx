import { useState } from "react";
import { uploadDocumentOrder } from "../api/client";
import type { Order } from "../api/client";

interface Props {
  onOrderCreated: () => void;
}

function friendlyError(raw: string): string {
  if (/not configured|contact support/i.test(raw))
    return "The extraction service is not available right now. Please contact support.";
  if (/busy|try again shortly/i.test(raw))
    return "The extraction service is temporarily busy. Please wait a moment and try again.";
  if (/could not reach|service returned an error/i.test(raw))
    return "Could not connect to the extraction service. Check your connection and try again.";
  if (/not a pdf|must be a pdf/i.test(raw))
    return "Only PDF files are supported. Please upload a .pdf document.";
  if (/exceeds/i.test(raw))
    return "The file is too large (max 10 MB). Please upload a smaller file.";
  if (/could not extract/i.test(raw))
    return "Could not find patient information in this document. Please check the file and try again.";
  if (/invalid credentials/i.test(raw))
    return "Your session has expired. Please sign in again.";
  return raw || "Something went wrong. Please try again.";
}

export default function Upload({ onOrderCreated }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [createdOrder, setCreatedOrder] = useState<Order | null>(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError("");
    setCreatedOrder(null);
    setUploading(true);
    try {
      const order = await uploadDocumentOrder(file);
      setCreatedOrder(order);
      setFile(null);
      onOrderCreated();
    } catch (err: unknown) {
      setError(friendlyError(err instanceof Error ? err.message : ""));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="upload-page">
      <h2>Upload Patient Document</h2>
      <form onSubmit={handleUpload} className="upload-form">
        <div className="field">
          <label>PDF Document</label>
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => {
              setFile(e.target.files?.[0] ?? null);
              setError("");
              setCreatedOrder(null);
            }}
            required
          />
        </div>
        <button type="submit" disabled={!file || uploading} className="btn-primary">
          {uploading ? "Creating order..." : "Upload & Create Order"}
        </button>
      </form>

      {error && (
        <div className="alert alert-error" role="alert">
          <span className="alert-icon">⚠</span>
          <span>{error}</span>
        </div>
      )}

      {createdOrder && (
        <div className="extraction-result">
          <h3>Order Created</h3>
          <table className="result-table">
            <tbody>
              <tr><td>First Name</td><td>{createdOrder.patient_first_name}</td></tr>
              <tr><td>Last Name</td><td>{createdOrder.patient_last_name}</td></tr>
              <tr><td>Date of Birth</td><td>{createdOrder.patient_dob}</td></tr>
              <tr><td>Status</td><td>{createdOrder.status}</td></tr>
              <tr><td>File</td><td>{createdOrder.document_filename ?? "Not recorded"}</td></tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
