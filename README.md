# Mansa — AI UGC Ads Generator

Web app to generate UGC-style ad videos (talking AI avatar + voice) from a
product description or script. Built with Next.js (App Router) and Supabase.

Live demo: https://mansa-six.vercel.app

## Stack

- **Next.js 16** (App Router, TypeScript, Tailwind CSS v4)
- **Supabase** — auth, Postgres, storage
- **Pluggable video provider** — `src/lib/video-provider.ts` abstracts the
  actual talking-avatar rendering (HeyGen, D-ID, Synthesia, ...). A mock
  provider is used by default so the app runs end-to-end without external
  API keys; wire up a real provider by setting `VIDEO_PROVIDER` and its
  credentials in `.env.local`.

## Getting started

```bash
npm install
cp .env.local.example .env.local   # fill in your Supabase project keys
npm run dev
```

Apply the database schema in `supabase/migrations/0001_init.sql` to your
Supabase project (via the SQL editor or `supabase db push`).

## Core flow

1. Sign up / log in (Supabase Auth).
2. Create a new ad: describe the product (or paste a URL), pick a tone.
3. A script is generated automatically (editable) via
   `src/lib/script-generator.ts` — swap in a real LLM call when you have an
   API key.
4. Pick an avatar + voice, launch generation.
5. Track status and download the finished video from the gallery.
