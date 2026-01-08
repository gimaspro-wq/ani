"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth/auth-context";
import { validateEmail, validatePassword, validatePasswordMatch, buildAuthUrl } from "@/lib/auth/validation";
import { BackendAPIError } from "@/lib/api/backend";
import { Button } from "@/components/ui/button";
import { Field, FieldContent, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field";
import { Navbar } from "@/components/blocks/navbar";
import { Footer } from "@/components/blocks/footer";
import { Spinner } from "@/components/ui/spinner";
import { toast } from "sonner";

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { register, isAuthenticated, isLoading: authLoading } = useAuth();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");

  const returnTo = searchParams.get("returnTo") || "/";

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.push(returnTo);
    }
  }, [isAuthenticated, authLoading, router, returnTo]);

  const handleValidateEmail = (email: string): boolean => {
    const result = validateEmail(email);
    setEmailError(result.error || "");
    return result.isValid;
  };

  const handleValidatePassword = (password: string): boolean => {
    const result = validatePassword(password);
    setPasswordError(result.error || "");
    return result.isValid;
  };

  const handleValidateConfirmPassword = (confirmPassword: string): boolean => {
    const result = validatePasswordMatch(password, confirmPassword);
    setConfirmPasswordError(result.error || "");
    return result.isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    // Validate fields
    const isEmailValid = handleValidateEmail(email);
    const isPasswordValid = handleValidatePassword(password);
    const isConfirmPasswordValid = handleValidateConfirmPassword(confirmPassword);
    
    if (!isEmailValid || !isPasswordValid || !isConfirmPasswordValid) {
      return;
    }

    setIsLoading(true);

    try {
      await register(email, password);
      toast.success("Account created successfully");
      router.push(returnTo);
    } catch (err) {
      if (err instanceof BackendAPIError) {
        if (err.status === 409 || err.status === 400) {
          setError(err.message || "Email is already registered");
        } else {
          setError(err.message || "Failed to create account. Please try again.");
        }
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex items-center justify-center min-h-[60vh]">
          <Spinner className="size-8 text-muted-foreground" />
        </div>
        <Footer />
      </div>
    );
  }

  if (isAuthenticated) {
    return null; // Will redirect via useEffect
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-4 py-12">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-heading text-foreground mb-2">
              Create Account
            </h1>
            <p className="text-muted-foreground">
              Sign up to start tracking your anime
            </p>
          </div>

          <div className="bg-foreground/5 border border-border rounded-lg p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                  {error}
                </div>
              )}

              <Field>
                <FieldLabel htmlFor="email">Email</FieldLabel>
                <FieldContent>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      setEmailError("");
                      setError("");
                    }}
                    onBlur={() => handleValidateEmail(email)}
                    disabled={isLoading}
                    className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground/20 disabled:opacity-50 disabled:cursor-not-allowed"
                    placeholder="you@example.com"
                    autoComplete="email"
                  />
                  {emailError && <FieldError>{emailError}</FieldError>}
                </FieldContent>
              </Field>

              <Field>
                <FieldLabel htmlFor="password">Password</FieldLabel>
                <FieldContent>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      setPasswordError("");
                      setError("");
                      // Re-validate confirm password if it has a value
                      if (confirmPassword) {
                        handleValidateConfirmPassword(confirmPassword);
                      }
                    }}
                    onBlur={() => handleValidatePassword(password)}
                    disabled={isLoading}
                    className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground/20 disabled:opacity-50 disabled:cursor-not-allowed"
                    placeholder="At least 6 characters"
                    autoComplete="new-password"
                  />
                  {passwordError && <FieldError>{passwordError}</FieldError>}
                  <FieldDescription>
                    Must be at least 6 characters long
                  </FieldDescription>
                </FieldContent>
              </Field>

              <Field>
                <FieldLabel htmlFor="confirmPassword">Confirm Password</FieldLabel>
                <FieldContent>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      setConfirmPasswordError("");
                      setError("");
                    }}
                    onBlur={() => handleValidateConfirmPassword(confirmPassword)}
                    disabled={isLoading}
                    className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground/20 disabled:opacity-50 disabled:cursor-not-allowed"
                    placeholder="Re-enter your password"
                    autoComplete="new-password"
                  />
                  {confirmPasswordError && <FieldError>{confirmPasswordError}</FieldError>}
                </FieldContent>
              </Field>

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <Spinner className="size-4 mr-2" />
                    Creating account...
                  </>
                ) : (
                  "Create Account"
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-muted-foreground">
                Already have an account?{" "}
                <Link
                  href={buildAuthUrl("/login", returnTo)}
                  className="text-foreground hover:underline font-medium"
                >
                  Sign in
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex items-center justify-center min-h-[60vh]">
          <Spinner className="size-8 text-muted-foreground" />
        </div>
        <Footer />
      </div>
    }>
      <RegisterForm />
    </Suspense>
  );
}
