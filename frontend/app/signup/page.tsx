"use client";

import { Logo } from "@/components/logo";
import { Button, TextInput } from "@/components/ui";
import { ApiError, client } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

export default function SignupPage() {
  const { setSession } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const rules = useMemo(
    () => [
      { label: "At least 8 characters", ok: password.length >= 8 },
      { label: "One letter", ok: /[A-Za-z]/.test(password) },
      { label: "One number", ok: /\d/.test(password) },
    ],
    [password],
  );

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (password !== confirm) {
      setError("Those passwords do not match.");
      return;
    }
    setPending(true);
    setError("");
    try {
      const result = await client.signup({ name, email, password, confirm_password: confirm });
      setSession(result.token, result.user);
      router.push("/library");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "We could not create the account. Try again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="hidden bg-navy px-12 py-12 text-white lg:block">
        <Logo className="[&_span]:text-white" />
        <p className="mt-16 font-display text-5xl leading-tight">A library with the page still attached.</p>
      </section>
      <section className="flex items-center px-6 py-12">
        <form onSubmit={submit} className="mx-auto w-full max-w-md">
          <Link href="/">
            <Logo className="lg:hidden" />
          </Link>
          <h1 className="mt-8 font-display text-4xl text-navy">Create your account</h1>
          <label className="mt-6 block text-sm font-semibold text-navy">
            Name
            <TextInput className="mt-1" value={name} onChange={(event) => setName(event.target.value)} required />
          </label>
          <label className="mt-4 block text-sm font-semibold text-navy">
            Email
            <TextInput className="mt-1" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className="mt-4 block text-sm font-semibold text-navy">
            Password
            <TextInput className="mt-1" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          <ul className="mt-2 space-y-1 text-xs">
            {rules.map((rule) => (
              <li key={rule.label} className={rule.ok ? "text-emerald-700" : "text-slate-500"}>
                {rule.ok ? "✓" : "•"} {rule.label}
              </li>
            ))}
          </ul>
          <label className="mt-4 block text-sm font-semibold text-navy">
            Confirm password
            <TextInput className="mt-1" type="password" value={confirm} onChange={(event) => setConfirm(event.target.value)} required />
          </label>
          {error ? <p className="mt-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          <Button type="submit" className="mt-6 w-full py-3" disabled={pending}>
            {pending ? "Creating account…" : "Sign up"}
          </Button>
          <p className="mt-4 text-sm text-slate-600">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-iris">
              Log in
            </Link>
          </p>
        </form>
      </section>
    </div>
  );
}
