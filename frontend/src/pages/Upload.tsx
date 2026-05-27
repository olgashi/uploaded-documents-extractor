import { useState } from "react";
import { extractDocument, createOrder } from "../api/client";
import type { ExtractionResult } from "../api/client";

interface Props {
  onOrderCreated: () => void;
}

export default function Upload({ onOrderCreated }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [extraction, setExtraction] = useState<ExtractionResult | null>(null);
  const [filename, setFilename] = useState("");
  const [error, setError] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [creating, setCreating] = useState(false);
  const [success, setSuccess] = useState(false);

  async function handleExtract(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError("");
    setExtraction(null);
    setSuccess(false);
    setExtracting(true);
    try {
      const result = await extractDocument(file);
      setExtraction(result.extraction);
      setFilename(result.filename);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Extraction failed");
    } finally {
      setExtracting(false);
    }
  }

  async function handleCreateOrder() {
    if (!extraction) return;
    setCreating(true);
    setError("");
    try {
      await createOrder({
        patient_first_name: extraction.first_name,
        patient_last_name: extraction.last_name,
        patient_dob: extraction.date_of_birth,
      });
      setSuccess(true);
      setExtraction(null);
      setFile(null);
      onOrderCreated();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create order");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="upload-page">
      <h2>Upload Patient Document</h2>
      <form onSubmit={handleExtract} className="upload-form">
        <div className="field">
          <label>PDF Document</label>
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
          />
        </div>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={!file || extracting} className="btn-primary">
          {extracting ? "Extracting…" : "Extract Patient Info"}
        </button>
      </form>

      {extraction && (
        <div className="extraction-result">
          <h3>Extracted Information</h3>
          <table className="result-table">
            <tbody>
              <tr><td>First Name</td><td>{extraction.first_name}</td></tr>
              <tr><td>Last Name</td><td>{extraction.last_name}</td></tr>
              <tr><td>Date of Birth</td><td>{extraction.date_of_birth}</td></tr>
              <tr><td>Filename</td><td>{filename}</td></tr>
            </tbody>
          </table>
          <button
            onClick={handleCreateOrder}
            disabled={creating}
            className="btn-primary"
          >
            {creating ? "Creating order…" : "Create Order"}
          </button>
        </div>
      )}

      {success && <p className="success">Order created successfully.</p>}
    </div>
  );
}
