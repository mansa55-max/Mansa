import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import type { AdProject } from "@/lib/types";
import { ProjectStatus } from "./project-status";

export default async function ProjectPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: project } = await supabase
    .from("ad_projects")
    .select("*")
    .eq("id", id)
    .single<AdProject>();

  if (!project) {
    notFound();
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-xl font-semibold">{project.product_name}</h1>
      <p className="mt-2 whitespace-pre-wrap text-sm text-neutral-600">{project.script}</p>
      <ProjectStatus initialProject={project} />
    </div>
  );
}
