"use client";

import { useState } from "react";
import { AVATARS, VOICES } from "@/lib/avatars";
import type { Tone } from "@/lib/types";
import { createAd } from "./actions";

const TONES: { value: Tone; label: string }[] = [
  { value: "excited", label: "Excited" },
  { value: "casual", label: "Casual" },
  { value: "professional", label: "Professional" },
  { value: "funny", label: "Funny" },
];

export function NewAdForm() {
  const [productName, setProductName] = useState("");
  const [productDescription, setProductDescription] = useState("");
  const [tone, setTone] = useState<Tone>("excited");
  const [script, setScript] = useState("");
  const [avatarId, setAvatarId] = useState(AVATARS[0].id);
  const [voiceId, setVoiceId] = useState(VOICES[0].id);
  const [isGeneratingScript, setIsGeneratingScript] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleGenerateScript() {
    if (!productName.trim()) return;
    setIsGeneratingScript(true);
    try {
      const res = await fetch("/api/generate-script", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ productName, productDescription, tone }),
      });
      const data = await res.json();
      if (data.script) setScript(data.script);
    } finally {
      setIsGeneratingScript(false);
    }
  }

  return (
    <form
      action={createAd}
      onSubmit={() => setIsSubmitting(true)}
      className="mt-6 flex flex-col gap-6"
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium" htmlFor="productName">
            Product name
          </label>
          <input
            id="productName"
            name="productName"
            required
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            className="rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900"
            placeholder="Glow Serum"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium" htmlFor="productUrl">
            Product URL (optional)
          </label>
          <input
            id="productUrl"
            name="productUrl"
            type="url"
            className="rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900"
            placeholder="https://yourstore.com/product"
          />
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium" htmlFor="productDescription">
          Product description
        </label>
        <textarea
          id="productDescription"
          name="productDescription"
          rows={3}
          value={productDescription}
          onChange={(e) => setProductDescription(e.target.value)}
          className="rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900"
          placeholder="A lightweight vitamin C serum that brightens skin in 2 weeks."
        />
      </div>

      <div className="flex flex-col gap-1">
        <span className="text-sm font-medium">Tone</span>
        <div className="flex flex-wrap gap-2">
          {TONES.map((t) => (
            <label
              key={t.value}
              className={`cursor-pointer rounded-full border px-3 py-1.5 text-sm ${
                tone === t.value
                  ? "border-neutral-900 bg-neutral-900 text-white"
                  : "border-neutral-300 text-neutral-600"
              }`}
            >
              <input
                type="radio"
                name="tone"
                value={t.value}
                checked={tone === t.value}
                onChange={() => setTone(t.value)}
                className="hidden"
              />
              {t.label}
            </label>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium" htmlFor="script">
            Script
          </label>
          <button
            type="button"
            onClick={handleGenerateScript}
            disabled={!productName.trim() || isGeneratingScript}
            className="text-sm font-medium text-neutral-900 underline disabled:text-neutral-300"
          >
            {isGeneratingScript ? "Generating…" : "Generate script"}
          </button>
        </div>
        <textarea
          id="script"
          name="script"
          rows={5}
          required
          value={script}
          onChange={(e) => setScript(e.target.value)}
          className="rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900"
          placeholder="Click “Generate script” or write your own"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium">Avatar</span>
          <div className="grid grid-cols-2 gap-2">
            {AVATARS.map((avatar) => (
              <label
                key={avatar.id}
                className={`cursor-pointer rounded-md border p-2 text-sm ${
                  avatarId === avatar.id ? "border-neutral-900" : "border-neutral-300"
                }`}
              >
                <input
                  type="radio"
                  name="avatarId"
                  value={avatar.id}
                  checked={avatarId === avatar.id}
                  onChange={() => setAvatarId(avatar.id)}
                  className="hidden"
                />
                <div className="font-medium">{avatar.name}</div>
                <div className="text-xs text-neutral-500">{avatar.style}</div>
              </label>
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium">Voice</span>
          <div className="grid grid-cols-2 gap-2">
            {VOICES.map((voice) => (
              <label
                key={voice.id}
                className={`cursor-pointer rounded-md border p-2 text-sm ${
                  voiceId === voice.id ? "border-neutral-900" : "border-neutral-300"
                }`}
              >
                <input
                  type="radio"
                  name="voiceId"
                  value={voice.id}
                  checked={voiceId === voice.id}
                  onChange={() => setVoiceId(voice.id)}
                  className="hidden"
                />
                <div className="font-medium">{voice.name}</div>
                <div className="text-xs text-neutral-500">{voice.language}</div>
              </label>
            ))}
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-md bg-neutral-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-neutral-700 disabled:opacity-60"
      >
        {isSubmitting ? "Generating your ad…" : "Generate video"}
      </button>
    </form>
  );
}
