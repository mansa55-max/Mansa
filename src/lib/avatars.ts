export interface Avatar {
  id: string;
  name: string;
  gender: "female" | "male";
  style: string;
}

export interface Voice {
  id: string;
  name: string;
  gender: "female" | "male";
  language: string;
}

// Static catalog for the MVP. Swap for a live catalog pulled from your
// video provider (e.g. HeyGen's /v2/avatars and /v2/voices) once configured.
export const AVATARS: Avatar[] = [
  { id: "avatar-mia", name: "Mia", gender: "female", style: "Casual, natural light" },
  { id: "avatar-jordan", name: "Jordan", gender: "male", style: "Studio, energetic" },
  { id: "avatar-sofia", name: "Sofia", gender: "female", style: "Outdoor, lifestyle" },
  { id: "avatar-leo", name: "Leo", gender: "male", style: "Home, cozy" },
];

export const VOICES: Voice[] = [
  { id: "voice-emma", name: "Emma", gender: "female", language: "en-US" },
  { id: "voice-marc", name: "Marc", gender: "male", language: "fr-FR" },
  { id: "voice-clara", name: "Clara", gender: "female", language: "fr-FR" },
  { id: "voice-noah", name: "Noah", gender: "male", language: "en-US" },
];
