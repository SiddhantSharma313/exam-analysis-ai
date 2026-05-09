"use client";

import { useState } from "react";

export default function Home() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uiMessage, setUiMessage] = useState(
    "Upload PDFs to start. Backend analysis will be connected in the next stage.",
  );

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const files = event.target.files ? Array.from(event.target.files) : [];
    const pdfFiles = files.filter((file) => file.type === "application/pdf");

    setSelectedFiles(pdfFiles);

    if (pdfFiles.length === 0) {
      setUiMessage("Please select one or more PDF files.");
      return;
    }

    setUiMessage(`${pdfFiles.length} PDF file(s) selected.`);
  }

  function handleAnalyzeClick() {
    setUiMessage(
      "Frontend ready. In the next stage we will connect this button to the Python backend.",
    );
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-8 px-6 py-10">
      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h1 className="text-2xl font-bold tracking-tight">
          Exam Analysis AI - MVP
        </h1>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
          Upload syllabus, previous year papers, assignments, and optional lab
          manuals in PDF format.
        </p>
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-semibold">1) Upload PDFs</h2>

        <label
          htmlFor="pdf-upload"
          className="mt-4 block rounded-lg border border-dashed border-zinc-400 p-6 text-center text-sm"
        >
          Choose one or more PDF files
          <input
            id="pdf-upload"
            type="file"
            accept="application/pdf"
            multiple
            className="mt-3 block w-full cursor-pointer text-sm"
            onChange={handleFileChange}
          />
        </label>

        <div className="mt-4">
          <h3 className="text-sm font-medium">Selected Files</h3>
          {selectedFiles.length === 0 ? (
            <p className="mt-2 text-sm text-zinc-500">No files selected yet.</p>
          ) : (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
              {selectedFiles.map((file) => (
                <li key={file.name}>{file.name}</li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-semibold">2) Run Analysis</h2>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
          This button is currently frontend-only. It will call the backend in
          the next stage.
        </p>
        <button
          type="button"
          onClick={handleAnalyzeClick}
          disabled={selectedFiles.length === 0}
          className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-zinc-400"
        >
          Analyze Documents
        </button>
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-semibold">Status</h2>
        <p className="mt-2 text-sm">{uiMessage}</p>
      </section>
    </main>
  );
}
