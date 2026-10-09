"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

const MAX_FILE_BYTES = 10 * 1024 * 1024;

type Mode = "text" | "image";

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmitted: () => void;
}

export function LogWorkoutModal({ open, onClose, onSubmitted }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [mode, setMode] = useState<Mode>("text");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  function reset() {
    setText("");
    setFile(null);
    setError(null);
    setMode("text");
  }

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0] ?? null;
    if (picked && picked.size > MAX_FILE_BYTES) {
      setError("Screenshot must be 10 MB or smaller.");
      setFile(null);
      e.target.value = "";
      return;
    }
    setError(null);
    setFile(picked);
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const input = mode === "text" ? { text: text.trim() } : { file: file ?? undefined };
    if (!input.text && !input.file) {
      setError(mode === "text" ? "Describe your workout first." : "Choose a screenshot first.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await api.logWorkout(input);
      reset();
      onSubmitted();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      className="m-auto w-full max-w-lg rounded-xl border border-zinc-200 bg-white p-0 text-zinc-900 shadow-xl backdrop:bg-black/40 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100"
    >
      <form onSubmit={onSubmit} className="space-y-4 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">Log a workout</h2>
            <p className="text-sm text-zinc-500">
              Our AI extracts the details. It appears in your feed within a few seconds.
            </p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close" className="text-zinc-400 hover:text-zinc-700">
            ✕
          </button>
        </div>

        <div role="tablist" className="grid grid-cols-2 gap-1 rounded-lg bg-zinc-100 p-1 text-sm dark:bg-zinc-800">
          {(["text", "image"] as const).map((m) => (
            <button
              key={m}
              type="button"
              role="tab"
              aria-selected={mode === m}
              onClick={() => {
                setMode(m);
                setError(null);
              }}
              className={`rounded-md px-3 py-1.5 font-medium transition ${
                mode === m ? "bg-white shadow-sm dark:bg-zinc-950" : "text-zinc-500 hover:text-zinc-800"
              }`}
            >
              {m === "text" ? "Describe it" : "Upload screenshot"}
            </button>
          ))}
        </div>

        {mode === "text" ? (
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={4}
            placeholder="e.g. Ran 5 km in 26 minutes this morning, average HR 152"
            className="input resize-none"
          />
        ) : (
          <label className="flex cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed border-zinc-300 px-4 py-8 text-center text-sm hover:border-emerald-500 dark:border-zinc-700">
            <span className="font-medium">{file ? file.name : "Choose an image"}</span>
            <span className="text-xs text-zinc-500">
              {file ? `${(file.size / 1024).toFixed(0)} KB` : "PNG or JPG from your watch or fitness app, up to 10 MB"}
            </span>
            <input type="file" accept="image/*" onChange={onFileChange} className="sr-only" />
          </label>
        )}

        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? "Submitting…" : "Log workout"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
