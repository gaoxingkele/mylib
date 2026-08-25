import { EyeIcon, MessageCircleIcon } from "lucide-react";
import { getModelCapabilities } from "@/lib/model-capabilities";
import { cn } from "@/lib/utils";

interface ModelCapabilityBadgesProps {
  label?: string | null;
  baseUrl?: string | null;
  model?: string | null;
  className?: string;
}

export function ModelCapabilityBadges({
  label,
  baseUrl,
  model,
  className,
}: ModelCapabilityBadgesProps) {
  const capabilities = getModelCapabilities({ label, baseUrl, model });
  const badgeClass =
    "inline-flex h-5 items-center justify-center rounded-md border border-neutral-300 bg-white text-neutral-600 dark:border-neutral-600 dark:bg-neutral-950 dark:text-neutral-300";

  return (
    <span
      className={cn("inline-flex shrink-0 items-center gap-0.5", className)}
    >
      {capabilities.chat && (
        <span className={cn(badgeClass, "min-w-5 px-1")} title="Chat model">
          <MessageCircleIcon className="size-3" />
        </span>
      )}
      {capabilities.vision && (
        <span className={cn(badgeClass, "min-w-5 px-1")} title="Vision input">
          <EyeIcon className="size-3" />
        </span>
      )}
    </span>
  );
}
