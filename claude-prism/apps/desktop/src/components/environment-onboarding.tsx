import {
  type ComponentType,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { open as shellOpen } from "@tauri-apps/plugin-shell";
import {
  AlertCircleIcon,
  CheckCircle2Icon,
  CircleIcon,
  DownloadIcon,
  FlaskConicalIcon,
  GitBranchIcon,
  KeyRoundIcon,
  Loader2Icon,
  RefreshCwIcon,
  TerminalIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ClaudeSetup } from "@/components/claude-setup";
import { useClaudeSetupStore } from "@/stores/claude-setup-store";
import { useUvSetupStore } from "@/stores/uv-setup-store";
import { cn } from "@/lib/utils";

type SetupItemState = "ready" | "loading" | "blocked" | "error";

interface SkillsStatus {
  installed: boolean;
  skill_count: number;
  location: string;
}

export function EnvironmentOnboarding() {
  const [initialCheckComplete, setInitialCheckComplete] = useState(false);
  const keepOpenDuringCheckRef = useRef(false);
  const [hasOpenedForSetup, setHasOpenedForSetup] = useState(false);
  const [completedDismissed, setCompletedDismissed] = useState(false);
  const [providerDialogOpen, setProviderDialogOpen] = useState(false);
  const [skillsStatus, setSkillsStatus] = useState<SkillsStatus | null>(null);
  const [skillsChecking, setSkillsChecking] = useState(true);
  const [skillsError, setSkillsError] = useState<string | null>(null);
  const [skillsDialogOpen, setSkillsDialogOpen] = useState(false);
  const [SkillsOnboardingComponent, setSkillsOnboardingComponent] =
    useState<ComponentType<{ onClose: () => void }> | null>(null);

  const claudeStatus = useClaudeSetupStore((s) => s.status);
  const claudeVersion = useClaudeSetupStore((s) => s.version);
  const claudeError = useClaudeSetupStore((s) => s.error);
  const isClaudeInstalling = useClaudeSetupStore((s) => s.isInstalling);
  const providerKind = useClaudeSetupStore((s) => s.providerKind);
  const claudeProviderConfigured = useClaudeSetupStore(
    (s) => s.claudeProviderConfigured,
  );
  const openAiCredentials = useClaudeSetupStore((s) => s.openAiCredentials);
  const checkClaudeStatus = useClaudeSetupStore((s) => s.checkStatus);
  const installClaude = useClaudeSetupStore((s) => s.install);

  const uvStatus = useUvSetupStore((s) => s.status);
  const uvVersion = useUvSetupStore((s) => s.version);
  const uvError = useUvSetupStore((s) => s.error);
  const isUvInstalling = useUvSetupStore((s) => s.isInstalling);
  const checkUvStatus = useUvSetupStore((s) => s.checkStatus);
  const installUv = useUvSetupStore((s) => s.install);
  const finishUvInstall = useUvSetupStore((s) => s._finishInstall);

  const checkSkillsStatus = useCallback(async () => {
    setSkillsChecking(true);
    setSkillsError(null);
    try {
      const status = await invoke<SkillsStatus>("check_skills_installed", {
        projectPath: null,
      });
      setSkillsStatus(status);
    } catch (err) {
      setSkillsStatus(null);
      setSkillsError(String(err));
    } finally {
      setSkillsChecking(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    Promise.allSettled([
      checkClaudeStatus(),
      checkUvStatus(),
      checkSkillsStatus(),
    ]).finally(() => {
      if (!cancelled) {
        setInitialCheckComplete(true);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [checkClaudeStatus, checkSkillsStatus, checkUvStatus]);

  useEffect(() => {
    const unlisten = listen<boolean>("uv-install-complete", (event) => {
      finishUvInstall(event.payload);
    });

    return () => {
      unlisten.then((fn) => fn());
    };
  }, [finishUvInstall]);

  const isClaudeInstalled =
    claudeStatus === "ready" || claudeStatus === "not-authenticated";
  const isClaudeReady = claudeStatus === "ready";
  const isUvReady = uvStatus === "ready";
  const isSkillsReady = !!skillsStatus?.installed;
  const claudeNeedsAttention =
    isClaudeInstalling || (claudeStatus !== "checking" && !isClaudeReady);
  const uvNeedsAttention =
    isUvInstalling || (uvStatus !== "checking" && !isUvReady);
  const skillsNeedsAttention =
    !skillsChecking && (!isSkillsReady || !!skillsError);
  const needsAttention =
    claudeNeedsAttention || uvNeedsAttention || skillsNeedsAttention;
  const isCheckingSetup =
    claudeStatus === "checking" || uvStatus === "checking" || skillsChecking;
  const setupComplete =
    initialCheckComplete && !needsAttention && !isCheckingSetup;
  const shouldShow =
    initialCheckComplete &&
    !completedDismissed &&
    (needsAttention ||
      (isCheckingSetup && keepOpenDuringCheckRef.current) ||
      hasOpenedForSetup);

  useEffect(() => {
    if (needsAttention) {
      keepOpenDuringCheckRef.current = true;
      setHasOpenedForSetup(true);
      setCompletedDismissed(false);
      return;
    }

    if (!isCheckingSetup) {
      keepOpenDuringCheckRef.current = false;
    }
  }, [isCheckingSetup, needsAttention]);

  const handleDone = () => {
    if (!setupComplete) return;
    keepOpenDuringCheckRef.current = false;
    setHasOpenedForSetup(false);
    setCompletedDismissed(true);
  };

  const openSkillsDialog = () => {
    setSkillsDialogOpen(true);
    if (!SkillsOnboardingComponent) {
      import(
        "@/components/scientific-skills/scientific-skills-onboarding"
      ).then((mod) =>
        setSkillsOnboardingComponent(() => mod.ScientificSkillsOnboarding),
      );
    }
  };

  const providerDetail = useMemo(() => {
    if (!isClaudeInstalled) {
      return "Install Claude Code before adding a provider";
    }
    if (!isClaudeReady) {
      return "Add an API key or sign in";
    }
    const openAiProviderCount = Math.max(
      openAiCredentials.length,
      providerKind === "openai-compatible" ? 1 : 0,
    );
    const includesClaudeProvider =
      claudeProviderConfigured || providerKind === "claude-code";
    const count = openAiProviderCount + (includesClaudeProvider ? 1 : 0);
    return `${count} provider${count === 1 ? "" : "s"} configured`;
  }, [
    claudeProviderConfigured,
    isClaudeInstalled,
    isClaudeReady,
    openAiCredentials.length,
    providerKind,
  ]);

  return (
    <>
      <Dialog open={shouldShow} onOpenChange={() => undefined}>
        <DialogContent
          showCloseButton={false}
          onEscapeKeyDown={(event) => event.preventDefault()}
          onInteractOutside={(event) => event.preventDefault()}
          className="w-[min(29rem,calc(100vw-2rem))] gap-0 overflow-hidden rounded-2xl border-border/70 p-0 shadow-xl sm:max-w-none"
        >
          <div className="flex flex-col items-center px-6 pt-6 pb-4 text-center">
            <img
              src="/icon-192.png"
              alt="ClaudePrism"
              className="size-14 object-contain"
            />
            <DialogHeader className="mt-3 items-center gap-1.5 text-center">
              <DialogTitle className="font-semibold text-xl">
                ClaudePrism
              </DialogTitle>
              <DialogDescription className="max-w-sm text-sm leading-relaxed">
                Set up the local tools and model provider required before
                entering the workspace.
              </DialogDescription>
            </DialogHeader>
          </div>

          <div className="px-4.5 pb-3">
            <div className="space-y-1.5">
              <SetupItem
                state={
                  isClaudeInstalling || claudeStatus === "checking"
                    ? "loading"
                    : claudeStatus === "error"
                      ? "error"
                      : isClaudeInstalled
                        ? "ready"
                        : "blocked"
                }
                icon={TerminalIcon}
                title="Claude Code"
                detail={
                  isClaudeInstalling
                    ? "Installing..."
                    : claudeStatus === "checking"
                      ? "Checking..."
                      : claudeStatus === "missing-git"
                        ? "Git for Windows is required first"
                        : claudeStatus === "not-installed"
                          ? "Required for AI writing"
                          : claudeStatus === "error"
                            ? claudeError || "Installation needs attention"
                            : claudeVersion
                              ? `Installed ${claudeVersion}`
                              : "Installed"
                }
                action={
                  claudeStatus === "missing-git"
                    ? {
                        label: "Git",
                        icon: GitBranchIcon,
                        onClick: () => {
                          shellOpen("https://git-scm.com/downloads/win");
                        },
                      }
                    : claudeStatus === "not-installed" ||
                        claudeStatus === "error"
                      ? {
                          label: isClaudeInstalling ? "Installing" : "Install",
                          icon: isClaudeInstalling ? Loader2Icon : DownloadIcon,
                          loading: isClaudeInstalling,
                          onClick: installClaude,
                        }
                      : {
                          label: "Check",
                          icon: RefreshCwIcon,
                          onClick: checkClaudeStatus,
                        }
                }
              />

              <SetupItem
                state={
                  isUvInstalling || uvStatus === "checking"
                    ? "loading"
                    : uvStatus === "error"
                      ? "error"
                      : isUvReady
                        ? "ready"
                        : "blocked"
                }
                icon={TerminalIcon}
                title="Python (uv)"
                detail={
                  isUvInstalling
                    ? "Installing..."
                    : uvStatus === "checking"
                      ? "Checking..."
                      : uvStatus === "not-installed"
                        ? "Required for Python workflows"
                        : uvStatus === "error"
                          ? uvError || "Installation needs attention"
                          : uvVersion || "Installed"
                }
                action={
                  uvStatus === "not-installed" || uvStatus === "error"
                    ? {
                        label: isUvInstalling ? "Installing" : "Install",
                        icon: isUvInstalling ? Loader2Icon : DownloadIcon,
                        loading: isUvInstalling,
                        onClick: installUv,
                      }
                    : {
                        label: "Check",
                        icon: RefreshCwIcon,
                        onClick: checkUvStatus,
                      }
                }
              />

              <SetupItem
                state={
                  claudeStatus === "checking"
                    ? "loading"
                    : claudeStatus === "error"
                      ? "error"
                      : isClaudeReady
                        ? "ready"
                        : "blocked"
                }
                icon={KeyRoundIcon}
                title="AI Provider"
                detail={providerDetail}
                action={
                  isClaudeInstalled
                    ? {
                        label: isClaudeReady ? "Manage" : "Configure",
                        icon: KeyRoundIcon,
                        onClick: () => setProviderDialogOpen(true),
                      }
                    : {
                        label: "Locked",
                        icon: KeyRoundIcon,
                        disabled: true,
                      }
                }
              />

              <SetupItem
                state={
                  skillsChecking
                    ? "loading"
                    : skillsError
                      ? "error"
                      : isSkillsReady
                        ? "ready"
                        : "blocked"
                }
                icon={FlaskConicalIcon}
                title="Scientific Skills"
                detail={
                  skillsChecking
                    ? "Checking..."
                    : skillsError
                      ? skillsError
                      : isSkillsReady
                        ? `${skillsStatus?.skill_count ?? 0} skills installed`
                        : "Required for scientific writing"
                }
                action={
                  skillsError
                    ? {
                        label: "Check",
                        icon: RefreshCwIcon,
                        onClick: checkSkillsStatus,
                      }
                    : {
                        label: isSkillsReady ? "Manage" : "Install",
                        icon: isSkillsReady ? FlaskConicalIcon : DownloadIcon,
                        onClick: openSkillsDialog,
                        disabled: skillsChecking,
                      }
                }
              />
            </div>
          </div>

          <div className="flex justify-center px-6 pt-1 pb-4">
            <Button
              disabled={!setupComplete}
              className="h-10 min-w-28 justify-center rounded-full px-7"
              onClick={handleDone}
            >
              Done
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={providerDialogOpen} onOpenChange={setProviderDialogOpen}>
        <DialogContent className="max-h-[85vh] w-[min(42rem,calc(100vw-2rem))] overflow-y-auto overflow-x-hidden sm:max-w-none">
          <DialogHeader>
            <DialogTitle>Add AI Provider</DialogTitle>
            <DialogDescription>
              Configure Anthropic or another model provider for this project.
            </DialogDescription>
          </DialogHeader>
          <ClaudeSetup
            variant="provider-dialog"
            onCancel={() => setProviderDialogOpen(false)}
            onSaved={() => {
              setProviderDialogOpen(false);
              checkClaudeStatus();
            }}
          />
        </DialogContent>
      </Dialog>

      {skillsDialogOpen && SkillsOnboardingComponent && (
        <SkillsOnboardingComponent
          onClose={() => {
            setSkillsDialogOpen(false);
            checkSkillsStatus();
          }}
        />
      )}
    </>
  );
}

function SetupItem({
  state,
  icon: Icon,
  title,
  detail,
  action,
}: {
  state: SetupItemState;
  icon: typeof TerminalIcon;
  title: string;
  detail: string;
  action?: {
    label: string;
    icon: typeof TerminalIcon;
    onClick?: () => void;
    loading?: boolean;
    disabled?: boolean;
  };
}) {
  const ActionIcon = action?.icon;

  return (
    <div className="grid min-h-[3.75rem] w-full max-w-full grid-cols-[2.25rem_minmax(0,1fr)_auto] items-center gap-2.5 overflow-hidden rounded-xl bg-muted/35 px-3 py-2.5 transition-colors hover:bg-muted/50">
      <div
        className={cn(
          "flex size-9 shrink-0 items-center justify-center",
          state === "ready" && "text-green-600 dark:text-green-400",
          state === "loading" && "text-muted-foreground",
          state === "blocked" && "text-muted-foreground/75",
          state === "error" && "text-destructive",
        )}
      >
        {state === "ready" ? (
          <CheckCircle2Icon className="size-6" />
        ) : state === "loading" ? (
          <Loader2Icon className="size-5 animate-spin" />
        ) : state === "error" ? (
          <AlertCircleIcon className="size-5" />
        ) : (
          <Icon className="size-5" />
        )}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-semibold text-sm">{title}</span>
          {state === "blocked" && (
            <CircleIcon className="size-2.5 shrink-0 text-muted-foreground/50" />
          )}
        </div>
        <p
          className={cn(
            "mt-0.5 truncate text-sm",
            state === "error" ? "text-destructive" : "text-muted-foreground",
          )}
          title={detail}
        >
          {detail}
        </p>
      </div>

      {action && (
        <Button
          type="button"
          variant={state === "ready" ? "outline" : "default"}
          size="sm"
          className="h-8 max-w-24 shrink-0 gap-1.5 rounded-lg px-2.5 text-sm"
          onClick={action.onClick}
          disabled={action.disabled || action.loading}
        >
          {ActionIcon && (
            <ActionIcon
              className={cn("size-3.5", action.loading && "animate-spin")}
            />
          )}
          {action.label}
        </Button>
      )}
    </div>
  );
}
