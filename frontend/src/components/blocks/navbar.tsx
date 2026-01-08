"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-context";
import { buildAuthUrl } from "@/lib/auth/validation";
import { CommandMenu } from "@/components/blocks/command-menu";
import { GitHubIcon, SearchIcon, MenuIcon, XIcon } from "@/components/ui/icons";
import { Kbd } from "@/components/ui/kbd";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

function UserAvatar({ email }: { email: string }) {
  // Get initials from email (first letter)
  const initial = email.charAt(0).toUpperCase();

  return (
    <div className="w-8 h-8 rounded-full bg-foreground text-background flex items-center justify-center text-sm font-medium">
      {initial}
    </div>
  );
}

export function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { isAuthenticated, user, logout, isSyncing, isLoading } = useAuth();
  const pathname = usePathname();

  return (
    <>
      <CommandMenu />
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border pt-[env(safe-area-inset-top)]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-14 items-center justify-between">
            <div className="flex items-center gap-8">
              <Link href="/" className="font-heading text-xl text-foreground">
                ani<span className="text-cyan">rohi</span>
              </Link>

              <div className="hidden md:flex items-center gap-6">
                <Link
                  href="/"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Home
                </Link>
                <Link
                  href="/browse"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Browse
                </Link>
                <Link
                  href="/search"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Search
                </Link>
                <Link
                  href="/library"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Library
                </Link>
                <Link
                  href="/schedule"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Schedule
                </Link>
                <Link
                  href="/saved"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Saved
                </Link>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  const event = new KeyboardEvent("keydown", {
                    key: "k",
                    metaKey: true,
                    bubbles: true,
                  });
                  document.dispatchEvent(event);
                }}
                className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-foreground/5 hover:bg-foreground/10 border border-border text-sm text-muted-foreground transition-colors"
              >
                <SearchIcon className="w-4 h-4" />
                <span>Search...</span>
                <Kbd className="ml-2">⌘K</Kbd>
              </button>

              <button
                onClick={() => {
                  const event = new KeyboardEvent("keydown", {
                    key: "k",
                    metaKey: true,
                    bubbles: true,
                  });
                  document.dispatchEvent(event);
                }}
                className="sm:hidden p-2 rounded-lg hover:bg-foreground/5 transition-colors"
                aria-label="Search"
              >
                <SearchIcon className="w-5 h-5 text-muted-foreground" />
              </button>

              {/* Sync indicator */}
              {isSyncing && (
                <div className="hidden sm:flex items-center gap-2 px-2 py-1 rounded-lg bg-cyan/10 border border-cyan/20">
                  <Spinner className="w-4 h-4 text-cyan" />
                  <span className="text-xs text-cyan">Syncing...</span>
                </div>
              )}

              <a
                href="https://github.com/noelrohi/anirohi"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg hover:bg-foreground/5 transition-colors"
                aria-label="GitHub"
              >
                <GitHubIcon className="w-5 h-5 text-muted-foreground" />
              </a>

              {/* Auth UI */}
              {isLoading ? (
                <div className="hidden md:block">
                  <Spinner className="w-5 h-5 text-muted-foreground" />
                </div>
              ) : isAuthenticated && user ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      className="flex items-center gap-2 p-1 rounded-lg hover:bg-foreground/5 transition-colors"
                      aria-label="User menu"
                    >
                      <UserAvatar email={user.email} />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <div className="px-3 py-2">
                      <p className="text-sm font-medium text-foreground">{user.email}</p>
                      <p className="text-xs text-muted-foreground">Logged in</p>
                    </div>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>
                      <Link href="/library" className="w-full">
                        Library
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={logout} className="text-destructive">
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <div className="hidden md:flex items-center gap-2">
                  <Button variant="ghost" size="sm" asChild>
                    <Link href={buildAuthUrl("/login", pathname)}>
                      Login
                    </Link>
                  </Button>
                  <Button size="sm" asChild>
                    <Link href={buildAuthUrl("/register", pathname)}>
                      Sign Up
                    </Link>
                  </Button>
                </div>
              )}

              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="md:hidden p-2 rounded-lg hover:bg-foreground/5 transition-colors"
                aria-label={isMenuOpen ? "Close menu" : "Open menu"}
              >
                {isMenuOpen ? (
                  <XIcon className="w-5 h-5 text-muted-foreground" />
                ) : (
                  <MenuIcon className="w-5 h-5 text-muted-foreground" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu panel */}
        {isMenuOpen && (
          <div className="md:hidden border-t border-border bg-background/95 backdrop-blur-md">
            <div className="px-4 py-4 space-y-1">
              <Link
                href="/"
                onClick={() => setIsMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-foreground/5 transition-colors"
              >
                Home
              </Link>
              <Link
                href="/browse"
                onClick={() => setIsMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-foreground/5 transition-colors"
              >
                Browse
              </Link>
              <Link
                href="/search"
                onClick={() => setIsMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-foreground/5 transition-colors"
              >
                Search
              </Link>
              <Link
                href="/library"
                onClick={() => setIsMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-foreground/5 transition-colors"
              >
                Library
              </Link>
              <Link
                href="/schedule"
                onClick={() => setIsMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-foreground/5 transition-colors"
              >
                Schedule
              </Link>
              <Link
                href="/saved"
                onClick={() => setIsMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-foreground/5 transition-colors"
              >
                Saved
              </Link>

              {/* Auth section for mobile */}
              {!isLoading && (
                <>
                  <div className="h-px my-2 bg-border" />
                  {isAuthenticated && user ? (
                    <>
                      <div className="px-3 py-2">
                        <p className="text-sm font-medium text-foreground">{user.email}</p>
                        <p className="text-xs text-muted-foreground">Logged in</p>
                      </div>
                      <button
                        onClick={() => {
                          logout();
                          setIsMenuOpen(false);
                        }}
                        className="w-full text-left px-3 py-2 rounded-lg text-sm text-destructive hover:bg-foreground/5 transition-colors"
                      >
                        Logout
                      </button>
                    </>
                  ) : (
                    <div className="flex gap-2 px-3 py-2">
                      <Button variant="outline" size="sm" className="flex-1" asChild>
                        <Link
                          href={buildAuthUrl("/login", pathname)}
                          onClick={() => setIsMenuOpen(false)}
                        >
                          Login
                        </Link>
                      </Button>
                      <Button size="sm" className="flex-1" asChild>
                        <Link
                          href={buildAuthUrl("/register", pathname)}
                          onClick={() => setIsMenuOpen(false)}
                        >
                          Sign Up
                        </Link>
                      </Button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </nav>
    </>
  );
}
