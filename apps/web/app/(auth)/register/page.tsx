"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ScanSearch, Sparkles, UploadCloud } from "lucide-react";
import { z } from "zod";

import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/lib/api-client";

const HIGHLIGHTS = [
  { icon: UploadCloud, label: "Upload PDFs, DOCX, or TXT — no setup required" },
  { icon: ScanSearch, label: "Automatic risk analysis across 12 clause categories" },
  { icon: Sparkles, label: "A LangGraph agent that shows its reasoning" },
];

const schema = z.object({
  full_name: z.string().min(1, "Your name is required."),
  organization_name: z.string().min(1, "Organization name is required."),
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(8, "Password must be at least 8 characters."),
});

type FormValues = z.infer<typeof schema>;

export default function RegisterPage() {
  const { register: registerAccount } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    try {
      await registerAccount(values);
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Unable to create your account.");
    }
  };

  return (
    <AuthShell
      title="Create your workspace"
      description="Set up ContractLens for your organization"
      imageSrc="https://images.unsplash.com/photo-1450101499163-c8848c66ca85?q=80&w=1600&auto=format&fit=crop"
      imageAlt="A person signing a printed contract at a desk"
      panelHeading="From raw contract to grounded answer in minutes."
      panelSubheading="Set up your workspace and start asking questions your legal team can trust — with a citation behind every word."
      highlights={HIGHLIGHTS}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="full_name">Full name</Label>
          <Input id="full_name" placeholder="Jordan Rivera" {...register("full_name")} />
          {errors.full_name && (
            <p className="text-sm text-destructive">{errors.full_name.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="organization_name">Organization</Label>
          <Input
            id="organization_name"
            placeholder="Acme Legal"
            {...register("organization_name")}
          />
          {errors.organization_name && (
            <p className="text-sm text-destructive">{errors.organization_name.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Work email</Label>
          <Input id="email" type="email" placeholder="you@company.com" {...register("email")} />
          {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" {...register("password")} />
          {errors.password && (
            <p className="text-sm text-destructive">{errors.password.message}</p>
          )}
        </div>
        {serverError && <p className="text-sm text-destructive">{serverError}</p>}
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Creating workspace..." : "Create workspace"}
        </Button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        Already have a workspace?{" "}
        <Link href="/login" className="font-medium text-foreground underline underline-offset-4">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
