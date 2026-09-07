export type AdStatus = "draft" | "generating" | "ready" | "failed";

export type Tone = "excited" | "casual" | "professional" | "funny";

export interface AdProject {
  id: string;
  user_id: string;
  product_name: string;
  product_description: string;
  product_url: string | null;
  tone: Tone;
  script: string;
  avatar_id: string;
  voice_id: string;
  status: AdStatus;
  video_url: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}
