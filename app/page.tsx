"use client";

import { useState } from "react";

type ImportanceTier = {
  highlyImportant: string[];
  mediumImportance: string[];
  lowImportance: string[];
  neverAsked: string[];
};

type TopicAnalysisResponse = {
  detectedTopics: string[];
  topicFrequency: Record<string, number>;
  filesAppearedIn: Record<string, string[]>;
  importanceTier: ImportanceTier;
  neverAskedTopics: string[];
  questionPatterns: {
    detectedQuestionPatterns: string[];
    patternFrequency: Record<string, number>;
    filesAppearedIn: Record<string, string[]>;
    relatedTopics: Record<string, string[]>;
    highFrequencyPatterns: string[];
  };
  aiMetadataSummary: {
    subject: string;
    filesAnalyzed: number;
    fileTypeBreakdown: Record<string, number>;
    topTopics: Array<{ topic: string; count: number }>;
    highFrequencyTopics: string[];
    questionPatterns: Record<string, number>;
    highFrequencyPatterns: string[];
    neverAskedTopics: string[];
  };
  aiAnalysis: {
    subjectType: string;
    highImportanceTopics: string[];
    mediumImportanceTopics: string[];
    lowImportanceTopics: string[];
    predictedImportantAreas: string[];
    highROIRevisionAreas: string[];
    recurringQuestionPatterns: string[];
    examStrategyInsights: string[];
    confidenceScore: string;
  };
};

export default function Home() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [analysisResult, setAnalysisResult] =
    useState<TopicAnalysisResponse | null>(null);
  const [uiMessage, setUiMessage] = useState(
    "Upload PDFs to start topic analysis.",
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

  async function handleAnalyzeClick() {
    if (selectedFiles.length === 0) {
      setUiMessage("Please select one or more PDF files.");
      return;
    }

    setIsUploading(true);
    setUiMessage("Uploading PDFs and running topic analysis...");
    setAnalysisResult(null);

    const formData = new FormData();

    selectedFiles.forEach((file) => {
      formData.append("files", file);
    });

    try {
      const response = await fetch("http://127.0.0.1:8000/analyze-topics", {
        method: "POST",
        body: formData,
      });

      const data = (await response.json()) as
        | TopicAnalysisResponse
        | { detail?: string };

      if (!response.ok) {
        const errorMessage =
          "detail" in data && data.detail
            ? data.detail
            : "Upload failed. Please try again.";
        setUiMessage(errorMessage);
        return;
      }

      const topicData = data as TopicAnalysisResponse;
      setAnalysisResult(topicData);
      setUiMessage(
        `Done. Detected ${topicData.detectedTopics.length} topic(s), ${topicData.questionPatterns.detectedQuestionPatterns.length} question pattern(s), and AI insights.`,
      );
    } catch {
      setUiMessage(
        "Could not connect to backend. Make sure FastAPI is running on port 8000.",
      );
    } finally {
      setIsUploading(false);
    }
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
          Click the button to send PDFs to the backend and organize topics by
          importance.
        </p>
        <button
          type="button"
          onClick={handleAnalyzeClick}
          disabled={selectedFiles.length === 0 || isUploading}
          className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-zinc-400"
        >
          {isUploading ? "Analyzing..." : "Analyze Topics"}
        </button>
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-semibold">Status</h2>
        <p className="mt-2 text-sm">{uiMessage}</p>
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-semibold">3) Topic Priority Results</h2>
        {!analysisResult ? (
          <p className="mt-2 text-sm text-zinc-500">
            Topic results will appear here after analysis.
          </p>
        ) : (
          <div className="mt-3 space-y-6 text-sm">
            <div>
              <h3 className="font-semibold">Highly Important</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {analysisResult.importanceTier.highlyImportant.map((topic) => (
                  <li key={`high-${topic}`}>
                    {topic} ({analysisResult.topicFrequency[topic] ?? 0}) -{" "}
                    {(analysisResult.filesAppearedIn[topic] ?? []).join(", ")}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="font-semibold">Medium Importance</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {analysisResult.importanceTier.mediumImportance.map((topic) => (
                  <li key={`medium-${topic}`}>
                    {topic} ({analysisResult.topicFrequency[topic] ?? 0}) -{" "}
                    {(analysisResult.filesAppearedIn[topic] ?? []).join(", ")}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="font-semibold">Low Importance</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {analysisResult.importanceTier.lowImportance.map((topic) => (
                  <li key={`low-${topic}`}>
                    {topic} ({analysisResult.topicFrequency[topic] ?? 0}) -{" "}
                    {(analysisResult.filesAppearedIn[topic] ?? []).join(", ")}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="font-semibold">Never Asked (from syllabus)</h3>
              {analysisResult.neverAskedTopics.length === 0 ? (
                <p className="mt-2 text-zinc-600 dark:text-zinc-300">
                  No never-asked topics found from uploaded syllabus files.
                </p>
              ) : (
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {analysisResult.neverAskedTopics.map((topic) => (
                    <li key={`never-${topic}`}>{topic}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-semibold">4) Question Pattern Detection</h2>
        {!analysisResult ? (
          <p className="mt-2 text-sm text-zinc-500">
            Question pattern results will appear here after analysis.
          </p>
        ) : analysisResult.questionPatterns.detectedQuestionPatterns.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-500">
            No question patterns detected. Upload at least one question paper PDF.
          </p>
        ) : (
          <div className="mt-3 space-y-6 text-sm">
            <div>
              <h3 className="font-semibold">Most Common Question Styles</h3>
              {analysisResult.questionPatterns.highFrequencyPatterns.length ===
              0 ? (
                <p className="mt-2 text-zinc-600 dark:text-zinc-300">
                  No high-frequency pattern yet.
                </p>
              ) : (
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {analysisResult.questionPatterns.highFrequencyPatterns.map(
                    (pattern) => (
                      <li key={`high-pattern-${pattern}`}>
                        {pattern} (
                        {analysisResult.questionPatterns.patternFrequency[pattern] ??
                          0}
                        )
                      </li>
                    ),
                  )}
                </ul>
              )}
            </div>

            <div>
              <h3 className="font-semibold">All Detected Pattern Categories</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5">
                {analysisResult.questionPatterns.detectedQuestionPatterns.map(
                  (pattern) => (
                    <li key={`pattern-${pattern}`}>
                      <p>
                        {pattern} (
                        {analysisResult.questionPatterns.patternFrequency[pattern] ??
                          0}
                        )
                      </p>
                      <p className="text-zinc-600 dark:text-zinc-300">
                        Files:{" "}
                        {(
                          analysisResult.questionPatterns.filesAppearedIn[pattern] ??
                          []
                        ).join(", ")}
                      </p>
                      <p className="text-zinc-600 dark:text-zinc-300">
                        Related topics:{" "}
                        {(analysisResult.questionPatterns.relatedTopics[pattern] ?? [])
                          .slice(0, 5)
                          .join(", ")}
                      </p>
                    </li>
                  ),
                )}
              </ul>
            </div>
          </div>
        )}
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-semibold">5) AI Analysis Insights</h2>
        {!analysisResult ? (
          <p className="mt-2 text-sm text-zinc-500">
            AI-ranked analysis will appear here after analysis.
          </p>
        ) : (
          <div className="mt-3 space-y-6 text-sm">
            <div>
              <h3 className="font-semibold">High ROI Revision Areas</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {analysisResult.aiAnalysis.highROIRevisionAreas.map((item) => (
                  <li key={`roi-${item}`}>{item}</li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="font-semibold">Predicted Important Areas</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {analysisResult.aiAnalysis.predictedImportantAreas.map((item) => (
                  <li key={`predicted-${item}`}>{item}</li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="font-semibold">AI-Ranked Topics</h3>
              <p className="mt-2 font-medium">High Importance</p>
              <ul className="mt-1 list-disc space-y-1 pl-5">
                {analysisResult.aiAnalysis.highImportanceTopics.map((item) => (
                  <li key={`ai-high-${item}`}>{item}</li>
                ))}
              </ul>
              <p className="mt-3 font-medium">Medium Importance</p>
              <ul className="mt-1 list-disc space-y-1 pl-5">
                {analysisResult.aiAnalysis.mediumImportanceTopics.map((item) => (
                  <li key={`ai-medium-${item}`}>{item}</li>
                ))}
              </ul>
              <p className="mt-3 font-medium">Low Importance</p>
              <ul className="mt-1 list-disc space-y-1 pl-5">
                {analysisResult.aiAnalysis.lowImportanceTopics.map((item) => (
                  <li key={`ai-low-${item}`}>{item}</li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="font-semibold">Recurring Question Styles (AI)</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {analysisResult.aiAnalysis.recurringQuestionPatterns.map((item) => (
                  <li key={`ai-pattern-${item}`}>{item}</li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="font-semibold">Strategy Insights</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {analysisResult.aiAnalysis.examStrategyInsights.map((item) => (
                  <li key={`ai-strategy-${item}`}>{item}</li>
                ))}
              </ul>
              <p className="mt-3">
                Confidence:{" "}
                <span className="font-medium">
                  {analysisResult.aiAnalysis.confidenceScore}
                </span>
              </p>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
