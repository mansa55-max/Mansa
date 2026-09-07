"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { getVideoProvider } from "@/lib/video-provider";
import type { Tone } from "@/lib/types";

export async function createAd(formData: FormData) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/new");
  }

  const productName = String(formData.get("productName") ?? "").trim();
  const productDescription = String(formData.get("productDescription") ?? "").trim();
  const productUrl = String(formData.get("productUrl") ?? "").trim() || null;
  const tone = String(formData.get("tone") ?? "excited") as Tone;
  const script = String(formData.get("script") ?? "").trim();
  const avatarId = String(formData.get("avatarId") ?? "");
  const voiceId = String(formData.get("voiceId") ?? "");

  const { data: project, error: insertError } = await supabase
    .from("ad_projects")
    .insert({
      user_id: user.id,
      product_name: productName,
      product_description: productDescription,
      product_url: productUrl,
      tone,
      script,
      avatar_id: avatarId,
      voice_id: voiceId,
      status: "generating",
    })
    .select()
    .single();

  if (insertError || !project) {
    throw new Error(insertError?.message ?? "Failed to create ad project");
  }

  try {
    const provider = getVideoProvider();
    const { videoUrl } = await provider.generate({ script, avatarId, voiceId });

    await supabase
      .from("ad_projects")
      .update({ status: "ready", video_url: videoUrl })
      .eq("id", project.id);
  } catch (err) {
    await supabase
      .from("ad_projects")
      .update({
        status: "failed",
        error_message: err instanceof Error ? err.message : "Generation failed",
      })
      .eq("id", project.id);
  }

  redirect(`/projects/${project.id}`);
}
