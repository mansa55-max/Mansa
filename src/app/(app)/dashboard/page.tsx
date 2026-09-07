import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import type { AdProject } from "@/lib/types";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-neutral-100 text-neutral-700",
  generating: "bg-amber-100 text-amber-700",
  ready: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: projects } = await supabase
    .from("ad_projects")
    .select("*")
    .order("created_at", { ascending: false })
    .returns<AdProject[]>();

  if (!projects || projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-neutral-300 bg-white py-20 text-center">
        <h2 className="text-lg font-semibold">No ads yet</h2>
        <p className="mt-1 max-w-sm text-sm text-neutral-500">
          Create your first AI UGC ad — describe your product, pick an avatar and voice,
          and we&apos;ll generate the video.
        </p>
        <Link
          href="/new"
          className="mt-4 rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700"
        >
          Create your first ad
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-xl font-semibold">Your ads</h1>
      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => (
          <Link
            key={project.id}
            href={`/projects/${project.id}`}
            className="rounded-xl border border-neutral-200 bg-white p-4 transition hover:border-neutral-400"
          >
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-medium">{project.product_name}</h3>
              <span
                className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[project.status]}`}
              >
                {project.status}
              </span>
            </div>
            <p className="mt-2 line-clamp-2 text-sm text-neutral-500">{project.script}</p>
            <p className="mt-3 text-xs text-neutral-400">
              {new Date(project.created_at).toLocaleDateString()}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
