/**
 * Validation utilities for auth forms
 */

export const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(email: string): { isValid: boolean; error?: string } {
  if (!email) {
    return { isValid: false, error: "Email is required" };
  }
  
  if (!EMAIL_REGEX.test(email)) {
    return { isValid: false, error: "Please enter a valid email address" };
  }
  
  return { isValid: true };
}

export function validatePassword(
  password: string,
  minLength = 6
): { isValid: boolean; error?: string } {
  if (!password) {
    return { isValid: false, error: "Password is required" };
  }
  
  if (password.length < minLength) {
    return {
      isValid: false,
      error: `Password must be at least ${minLength} characters`,
    };
  }
  
  return { isValid: true };
}

export function validatePasswordMatch(
  password: string,
  confirmPassword: string
): { isValid: boolean; error?: string } {
  if (!confirmPassword) {
    return { isValid: false, error: "Please confirm your password" };
  }
  
  if (confirmPassword !== password) {
    return { isValid: false, error: "Passwords do not match" };
  }
  
  return { isValid: true };
}

/**
 * Build a login/register URL with returnTo parameter
 */
export function buildAuthUrl(
  path: "/login" | "/register",
  returnTo?: string | null
): string {
  if (!returnTo || returnTo === "/") {
    return path;
  }
  return `${path}?returnTo=${encodeURIComponent(returnTo)}`;
}
