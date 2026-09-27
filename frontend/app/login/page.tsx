"use client";

import { Logo } from "@/components/logo";
import { Button, TextInput } from "@/components/ui";
import { ApiError, client } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export default function LoginPage() {
  const { setSession } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const result = await client.login({ email, password });
      setSession(result.token, result.user);
      router.push("/library");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "We could not sign you in. Try again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="hidden bg-navy px-12 py-12 text-white lg:block">
        <Logo className="[&_span]:text-white" />
        <p className="mt-16 font-display text-5xl leading-tight">Ask questions. See the evidence.</p>
        <p className="mt-4 max-w-md text-slate-200">Every answer stays tied to a page, a section, and the original wording.</p>
      </section>
      <section className="flex items-center px-6 py-12">
        <form onSubmit={submit} className="mx-auto w-full max-w-md">
          <Link href="/">
            <Logo className="lg:hidden" />
          </Link>
          <h1 className="mt-8 font-display text-4xl text-navy">Welcome back</h1>
          <p className="mt-2 text-sm text-slate-600">Log in to your document library.</p>
          <label className="mt-6 block text-sm font-semibold text-navy">
            Email
            <TextInput className="mt-1" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className="mt-4 block text-sm font-semibold text-navy">
            Password
            <TextInput className="mt-1" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          {error ? <p className="mt-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          <Button type="submit" className="mt-6 w-full py-3" disabled={pending}>
            {pending ? "Signing in…" : "Log in"}
          </Button>
          <p className="mt-4 text-sm text-slate-600">
            New to DocuLens?{" "}
            <Link href="/signup" className="font-semibold text-iris">
              Create an account
            </Link>
          </p>
          <p className="mt-2 text-sm text-slate-600">
            Or{" "}
            <Link href="/demo" className="font-semibold text-iris">
              try the demo
            </Link>{" "}
            without an account.
          </p>
        </form>
      </section>
    </div>
  );
}
