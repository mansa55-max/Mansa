import Link from "next/link";
import { signUp } from "../actions";

export default async function SignupPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;

  return (
    <div className="mx-auto flex min-h-[80vh] w-full max-w-sm flex-col justify-center px-4">
      <h1 className="text-2xl font-semibold">Create an account</h1>
      <p className="mt-1 text-sm text-neutral-500">
        Start generating UGC ads in minutes.
      </p>

      {error && (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}

      <form action={signUp} className="mt-6 flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor="email" className="text-sm font-medium">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            className="rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="password" className="text-sm font-medium">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            minLength={6}
            required
            className="rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900"
          />
        </div>
        <button
          type="submit"
          className="mt-2 rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700"
        >
          Sign up
        </button>
      </form>

      <p className="mt-6 text-sm text-neutral-500">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-neutral-900 underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
