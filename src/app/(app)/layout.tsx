import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { signOut } from "../(auth)/actions";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="border-b border-neutral-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link href="/dashboard" className="text-lg font-semibold">
            Mansa
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/dashboard" className="text-neutral-600 hover:text-neutral-900">
              Dashboard
            </Link>
            <Link
              href="/new"
              className="rounded-md bg-neutral-900 px-3 py-1.5 font-medium text-white hover:bg-neutral-700"
            >
              New ad
            </Link>
            {user && (
              <form action={signOut}>
                <button className="text-neutral-500 hover:text-neutral-900">Log out</button>
              </form>
            )}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
    </div>
  );
}
