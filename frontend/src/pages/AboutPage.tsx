import { Card } from "../components/ui";
import { ShieldCheck } from "lucide-react";

export function AboutPage() {
  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">About DefenceVision</h1>
        <p className="text-sm text-slate-400">
          AI-powered geospatial infrastructure change assessment platform
        </p>
      </div>

      <Card title="Purpose">
        <p className="text-sm leading-relaxed text-slate-300">
          DefenceVision is a research/academic prototype that assists analysts in identifying and
          reviewing visual infrastructure changes between multi-temporal geospatial images. It
          combines classical computer vision with a modular architecture ready for deep-learning
          models, human-in-the-loop review, geospatial visualisation and automated reporting.
        </p>
      </Card>

      <Card title="How the pipeline works">
        <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-300">
          <li>Preprocessing — resolution, noise and contrast normalisation</li>
          <li>Registration — ORB feature matching with RANSAC homography (identity fallback)</li>
          <li>Change detection — aligned difference, Otsu threshold, morphology, components</li>
          <li>Classification — heuristic broad infrastructure categories</li>
          <li>Severity & confidence — transparent algorithmic scoring</li>
          <li>Analyst review, geospatial map and PDF reporting</li>
        </ol>
      </Card>

      <Card title="Scope & Responsible Use">
        <ul className="space-y-1 text-sm text-slate-300">
          <li>• AI assists the analyst — it never replaces human judgement.</li>
          <li>• No weapon targeting, autonomous targeting or offensive decision-making.</li>
          <li>• No facial recognition, individual tracking or personnel identification.</li>
          <li>• Findings are presented as "potential" visual changes requiring verification.</li>
        </ul>
        <div className="mt-4 flex items-center gap-2 rounded-md bg-base-950 p-3">
          <ShieldCheck className="h-5 w-5 text-accent" />
          <p className="text-xs text-slate-400">
            Confidence values are algorithmic measures of visual signal strength, not probabilistic
            model outputs. Limited to available imagery resolution.
          </p>
        </div>
      </Card>
    </div>
  );
}
