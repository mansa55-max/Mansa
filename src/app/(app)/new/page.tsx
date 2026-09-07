import { NewAdForm } from "./new-ad-form";

export default function NewAdPage() {
  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-xl font-semibold">Create a new UGC ad</h1>
      <p className="mt-1 text-sm text-neutral-500">
        Describe your product, generate a script, then pick an avatar and voice to render
        your video.
      </p>
      <NewAdForm />
    </div>
  );
}
