"use client";

import * as React from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";

interface DropdownMenuContextType {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

const DropdownMenuContext = React.createContext<DropdownMenuContextType | undefined>(undefined);

export function DropdownMenu({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <DropdownMenuContext.Provider value={{ isOpen, setIsOpen }}>
      <div className="relative">{children}</div>
    </DropdownMenuContext.Provider>
  );
}

export function DropdownMenuTrigger({
  children,
  asChild,
}: {
  children: React.ReactNode;
  asChild?: boolean;
}) {
  const context = React.useContext(DropdownMenuContext);
  if (!context) throw new Error("DropdownMenuTrigger must be used within DropdownMenu");

  const { isOpen, setIsOpen } = context;

  if (asChild && React.isValidElement(children)) {
    const childProps = children.props as Record<string, unknown>;
    return React.cloneElement(children, {
      onClick: (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsOpen(!isOpen);
        if (typeof childProps.onClick === "function") {
          childProps.onClick(e);
        }
      },
    } as React.HTMLAttributes<HTMLElement>);
  }

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        setIsOpen(!isOpen);
      }}
      className="outline-none"
    >
      {children}
    </button>
  );
}

export function DropdownMenuContent({
  children,
  align = "end",
  className,
}: {
  children: React.ReactNode;
  align?: "start" | "end";
  className?: string;
}) {
  const context = React.useContext(DropdownMenuContext);
  if (!context) throw new Error("DropdownMenuContent must be used within DropdownMenu");

  const { isOpen, setIsOpen } = context;
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  React.useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest("[data-dropdown-menu]")) {
        setIsOpen(false);
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    };

    document.addEventListener("click", handleClickOutside);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("click", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, setIsOpen]);

  if (!isOpen || !mounted) return null;

  return createPortal(
    <div
      data-dropdown-menu
      className={cn(
        "absolute z-50 min-w-[12rem] rounded-lg border border-border bg-background/95 backdrop-blur-md p-1 shadow-lg",
        "animate-in fade-in-0 zoom-in-95",
        align === "end" ? "right-0" : "left-0",
        className
      )}
      style={{
        position: "absolute",
        top: "100%",
        marginTop: "0.5rem",
      }}
    >
      {children}
    </div>,
    document.body
  );
}

export function DropdownMenuItem({
  children,
  onClick,
  className,
  disabled,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
}) {
  const context = React.useContext(DropdownMenuContext);
  if (!context) throw new Error("DropdownMenuItem must be used within DropdownMenu");

  const { setIsOpen } = context;

  return (
    <button
      onClick={() => {
        if (!disabled && onClick) {
          onClick();
          setIsOpen(false);
        }
      }}
      disabled={disabled}
      className={cn(
        "w-full text-left px-3 py-2 text-sm rounded-md transition-colors",
        "hover:bg-foreground/5 focus:bg-foreground/5 outline-none",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        className
      )}
    >
      {children}
    </button>
  );
}

export function DropdownMenuSeparator({ className }: { className?: string }) {
  return (
    <div
      className={cn("h-px my-1 bg-border", className)}
      role="separator"
      aria-orientation="horizontal"
    />
  );
}
