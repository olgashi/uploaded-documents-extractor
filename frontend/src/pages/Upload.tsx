import { useState } from "react";
import { extractDocument, createOrder } from "../api/client";
import type { ExtractionResult } from "../api/client";

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
      setError(friendlyError(err instanceof Error ? err.message : ""));
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
      setError(friendlyError(err instanceof Error ? err.message : ""));
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
            onChange={(e) => {
              setFile(e.target.files?.[0] ?? null);
              setError("");
              setExtraction(null);
            }}
            required
          />
        </div>
        <button type="submit" disabled={!file || extracting} className="btn-primary">
          {extracting ? "Extracting…" : "Extract Patient Info"}
        </button>
      </form>

      {error && (
        <div className="alert alert-error" role="alert">
          <span className="alert-icon">⚠</span>
          <span>{error}</span>
        </div>
      )}

      {extraction && (
        <div className="extraction-result">
          <h3>Extracted Information</h3>
          <p className="extraction-hint">Please review before creating the order.</p>
          <table className="result-table">
            <tbody>
              <tr><td>First Name</td><td>{extraction.first_name}</td></tr>
              <tr><td>Last Name</td><td>{extraction.last_name}</td></tr>
              <tr><td>Date of Birth</td><td>{extraction.date_of_birth}</td></tr>
              <tr><td>File</td><td>{filename}</td></tr>
            </tbody>
          </table>
          <button
            onClick={handleCreateOrder}
            disabled={creating}
            className="btn-primary"
          >
            {creating ? "Creating order…" : "Confirm & Create Order"}
          </button>
        </div>
      )}

      {success && (
        <div className="alert alert-success" role="status">
          <span className="alert-icon">✓</span>
          <span>Order created successfully.</span>
        </div>
      )}
    </div>
  );
}
