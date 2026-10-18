"use client";

import { cn } from "@/lib/utils";
import { Sparkles } from "lucide-react";

export interface DisplayCardProps {
  className?: string;
  icon?: React.ReactNode;
  title?: string;
  description?: string;
  date?: string;
  iconClassName?: string;
  titleClassName?: string;
  /** Makes the card an accessible button (used for "point a doc" selection). */
  onClick?: () => void;
  /** Highlighted / chosen state: colour restored, glowing border. */
  selected?: boolean;
  /** Optional trailing element in the title row (e.g. a check mark). */
  trailing?: React.ReactNode;
}

export function DisplayCard({
  className,
  icon = <Sparkles className="size-4 text-blue-300" />,
  title = "Featured",
  description = "Discover amazing content",
  date = "Just now",
  iconClassName = "text-blue-500",
  titleClassName = "text-blue-500",
  onClick,
  selected,
  trailing,
}: DisplayCardProps) {
  const interactive = typeof onClick === "function";
  return (
    <div
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      aria-pressed={interactive ? !!selected : undefined}
      onClick={onClick}
      onKeyDown={
        interactive
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick?.();
              }
            }
          : undefined
      }
      className={cn(
        "relative flex h-36 w-[22rem] -skew-y-[8deg] select-none flex-col justify-between rounded-xl border-2 bg-muted/70 backdrop-blur-sm px-4 py-3 transition-all duration-700 after:absolute after:-right-1 after:top-[-5%] after:h-[110%] after:w-[20rem] after:bg-gradient-to-l after:from-background after:to-transparent after:content-[''] hover:border-white/20 hover:bg-muted [&>*]:flex [&>*]:items-center [&>*]:gap-2",
        interactive && "cursor-pointer",
        selected &&
          "border-sky/70 bg-muted shadow-[0_0_0_1px_var(--ring-soft),0_18px_40px_-18px_var(--ring-soft)] hover:border-sky/80",
        className
      )}
    >
      <div>
        <span className={cn("relative inline-block rounded-full bg-blue-800 p-1", iconClassName)}>
          {icon}
        </span>
        <p className={cn("min-w-0 flex-1 truncate text-lg font-medium", titleClassName)} title={title}>
          {title}
        </p>
        {trailing}
      </div>
      <p className="whitespace-nowrap text-lg">{description}</p>
      <p className="text-muted-foreground">{date}</p>
    </div>
  );
}

/** Tailwind classes that stack up to three cards on the same grid cell, skewed. */
export function stackClass(index: number, dimmed = true): string {
  const dim = dimmed
    ? "grayscale-[100%] before:absolute before:w-[100%] before:outline-1 before:rounded-xl before:outline-border before:h-[100%] before:content-[''] before:bg-blend-overlay before:bg-background/50 hover:before:opacity-0 before:transition-opacity before:duration-700 hover:grayscale-0 before:left-0 before:top-0"
    : "";
  switch (index) {
    case 0:
      return `[grid-area:stack] hover:-translate-y-10 ${dim}`;
    case 1:
      return `[grid-area:stack] translate-x-16 translate-y-10 hover:-translate-y-1 ${dim}`;
    default:
      return "[grid-area:stack] translate-x-32 translate-y-20 hover:translate-y-10";
  }
}

interface DisplayCardsProps {
  cards?: DisplayCardProps[];
}

export default function DisplayCards({ cards }: DisplayCardsProps) {
  const defaultCards: DisplayCardProps[] = [
    { className: stackClass(0) },
    { className: stackClass(1) },
    { className: stackClass(2) },
  ];

  const displayCards = cards || defaultCards;

  return (
    <div className="grid [grid-template-areas:'stack'] place-items-center opacity-100 animate-in fade-in-0 duration-700">
      {displayCards.map((cardProps, index) => (
        <DisplayCard key={index} {...cardProps} />
      ))}
    </div>
  );
}
