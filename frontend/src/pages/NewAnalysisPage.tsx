import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import { ArrowRight, CheckCircle2, Loader2, UploadCloud, X } from "lucide-react";
import { api } from "../api/client";
import type { Analysis } from "../types";
import { Card } from "../components/ui";

interface FormState {
  name: string;
  area: string;
  latitude: string;
  longitude: string;
  description: string;
  analyst: string;
}

export function NewAnalysisPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<FormState>({
    name: "",
    area: "",
    latitude: "",
    longitude: "",
    description: "",
    analyst: "",
  });
  const [beforeFile, setBeforeFile] = useState<File | null>(null);
  const [afterFile, setAfterFile] = useState<File | null>(null);
  const [beforeUrl, setBeforeUrl] = useState<string | null>(null);
  const [afterUrl, setAfterUrl] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState<"form" | "upload" | "processing">("form");
  const [error, setError] = useState("");

  const onBefore = useCallback((files: File[]) => {
    if (files[0]) {
      setBeforeFile(files[0]);
      setBeforeUrl(URL.createObjectURL(files[0]));
    }
  }, []);
  const onAfter = useCallback((files: File[]) => {
    if (files[0]) {
      setAfterFile(files[0]);
      setAfterUrl(URL.createObjectURL(files[0]));
    }
  }, []);

  const beforeDrop = useDropzone({ onDrop: onBefore, accept: { "image/*": [] }, maxFiles: 1 });
  const afterDrop = useDropzone({ onDrop: onAfter, accept: { "image/*": [] }, maxFiles: 1 });

  async function createAndUpload() {
    setError("");
    setBusy(true);
    try {
      const created = await api.createAnalysis({
        name: form.name,
        area: form.area || null,
        latitude: form.latitude ? parseFloat(form.latitude) : null,
        longitude: form.longitude ? parseFloat(form.longitude) : null,
        description: form.description || null,
        analyst: form.analyst || null,
      });
      setAnalysis(created);
      setStep("upload");

      if (beforeFile) await api.uploadImage(created.id, "before", beforeFile);
      if (afterFile) await api.uploadImage(created.id, "after", afterFile);

      setStep("processing");
      await api.process(created.id);
      // Give the background task a moment, then navigate.
      setTimeout(() => navigate(`/analyses/${created.id}`), 1200);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  const canSubmit =
    form.name.trim().length > 0 &&
    beforeFile !== null &&
    afterFile !== null;

  if (step === "processing") {
    return (
      <Card title="Starting Analysis">
        <div className="flex flex-col items-center gap-4 py-16">
          <Loader2 className="h-10 w-10 animate-spin text-accent" />
          <p className="text-sm text-slate-300">
            Analysing imagery #{analysis?.id} — you will be redirected to the results shortly.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">New Analysis</h1>
        <p className="text-sm text-slate-400">Define the project, then provide before/after imagery.</p>
      </div>

      {error && (
        <div className="rounded-md border border-red-800 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {step === "form" && (
        <Card title="Analysis Information">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="md:col-span-2">
              <label className="label">Analysis Name *</label>
              <input
                className="input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. Coastal Construction Survey – Q3"
              />
            </div>
            <div>
              <label className="label">Area Name</label>
              <input
                className="input"
                value={form.area}
                onChange={(e) => setForm({ ...form, area: e.target.value })}
                placeholder="e.g. Sector 7, River District"
              />
            </div>
            <div>
              <label className="label">Analyst Name</label>
              <input
                className="input"
                value={form.analyst}
                onChange={(e) => setForm({ ...form, analyst: e.target.value })}
                placeholder="Analyst"
              />
            </div>
            <div>
              <label className="label">Latitude (optional)</label>
              <input
                className="input"
                value={form.latitude}
                onChange={(e) => setForm({ ...form, latitude: e.target.value })}
                placeholder="e.g. 39.9042"
              />
            </div>
            <div>
              <label className="label">Longitude (optional)</label>
              <input
                className="input"
                value={form.longitude}
                onChange={(e) => setForm({ ...form, longitude: e.target.value })}
                placeholder="e.g. 116.4074"
              />
            </div>
            <div className="md:col-span-2">
              <label className="label">Description</label>
              <textarea
                className="input"
                rows={3}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Optional context for this analysis"
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button className="btn-primary" onClick={() => setStep("upload")} disabled={!form.name.trim()}>
              Continue to Imagery <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </Card>
      )}

      {step === "upload" && (
        <Card
          title="Upload Imagery"
          subtitle="Supported formats: JPG, JPEG, PNG, TIFF. Max 25 MB each."
          actions={
            <button className="btn-ghost !py-1.5 text-xs" onClick={() => setStep("form")}>
              Back
            </button>
          }
        >
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <DropSlot
              drop={beforeDrop}
              title="Before Image"
              file={beforeFile}
              preview={beforeUrl}
              onClear={() => {
                setBeforeFile(null);
                setBeforeUrl(null);
              }}
            />
            <DropSlot
              drop={afterDrop}
              title="After Image"
              file={afterFile}
              preview={afterUrl}
              onClear={() => {
                setAfterFile(null);
                setAfterUrl(null);
              }}
            />
          </div>

          <div className="mt-6 flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Both images are required before processing can begin.
            </p>
            <div className="flex gap-2">
              {analysis && (
                <button className="btn-ghost" onClick={() => navigate(`/analyses/${analysis.id}`)}>
                  Start Without Processing
                </button>
              )}
              <button className="btn-primary" onClick={createAndUpload} disabled={!canSubmit || busy}>
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                Create & Process
              </button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

function DropSlot({
  drop,
  title,
  file,
  preview,
  onClear,
}: {
  drop: ReturnType<typeof useDropzone>;
  title: string;
  file: File | null;
  preview: string | null;
  onClear: () => void;
}) {
  return (
    <div>
      <label className="label">{title}</label>
      <div
        {...drop.getRootProps()}
        className={`relative flex h-56 flex-col items-center justify-center rounded-lg border-2 border-dashed p-4 text-center transition-colors ${
          drop.isDragActive ? "border-accent bg-accent/10" : "border-base-700 bg-base-950"
        }`}
      >
        <input {...drop.getInputProps()} />
        {file ? (
          <>
            <img src={preview || ""} alt={title} className="absolute inset-0 h-full w-full rounded-lg object-cover" />
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onClear();
              }}
              className="absolute right-2 top-2 rounded-full bg-base-900/90 p-1 text-slate-300 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
            <div className="absolute bottom-2 left-2 rounded bg-base-900/90 px-2 py-1 text-xs text-slate-200">
              {file.name}
            </div>
          </>
        ) : (
          <>
            <UploadCloud className="mb-2 h-8 w-8 text-slate-500" />
            <p className="text-sm text-slate-400">Drop image here or click to browse</p>
            <p className="mt-1 text-xs text-slate-600">JPG · PNG · TIFF</p>
          </>
        )}
      </div>
    </div>
  );
}
