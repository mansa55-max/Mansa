import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-24 text-center">
      <span className="rounded-full bg-neutral-100 px-3 py-1 text-xs font-medium text-neutral-600">
        AI UGC ads, no camera required
      </span>
      <h1 className="mt-6 max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
        Turn a product description into a UGC ad in minutes
      </h1>
      <p className="mt-4 max-w-xl text-neutral-500">
        Mansa writes the script, picks a talking AI avatar and voice, and renders a
        ready-to-post UGC-style ad video — no filming, no creators to manage.
      </p>
      <div className="mt-8 flex gap-3">
        <Link
          href="/signup"
          className="rounded-md bg-neutral-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-neutral-700"
        >
          Get started free
        </Link>
        <Link
          href="/login"
          className="rounded-md border border-neutral-300 px-5 py-2.5 text-sm font-medium hover:border-neutral-500"
        >
          Log in
        </Link>
      </div>
    </div>
  );
}
