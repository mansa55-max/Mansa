"use client";

import { useEffect, useState } from "react";
import type { AdProject } from "@/lib/types";

export function ProjectStatus({ initialProject }: { initialProject: AdProject }) {
  const [project, setProject] = useState(initialProject);

  useEffect(() => {
    if (project.status !== "generating") return;

    const interval = setInterval(async () => {
      const res = await fetch(`/api/projects/${project.id}`);
      if (!res.ok) return;
      const { project: updated } = await res.json();
      setProject(updated);
    }, 3000);

    return () => clearInterval(interval);
  }, [project.status, project.id]);

  return (
    <div className="mt-6 rounded-xl border border-neutral-200 bg-white p-6">
      {project.status === "generating" && (
        <div className="flex items-center gap-3 text-sm text-neutral-600">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-neutral-300 border-t-neutral-900" />
          Rendering your video… this usually takes under a minute.
        </div>
      )}

      {project.status === "failed" && (
        <div className="text-sm text-red-600">
          Generation failed{project.error_message ? `: ${project.error_message}` : "."}
        </div>
      )}

      {project.status === "ready" && project.video_url && (
        <div className="flex flex-col gap-4">
          <video
            src={project.video_url}
            controls
            className="aspect-[9/16] w-full max-w-xs rounded-lg bg-black"
          />
          <a
            href={project.video_url}
            download
            className="w-fit rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700"
          >
            Download video
          </a>
        </div>
      )}
    </div>
  );
}
