"use client";

import { useMemo, useState } from "react";
import { Check, ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { PROJECT_OPTIONS } from "./context-data";

function ColumnHeading({ children }: { children: string }) {
  return (
    <div className="px-2 pb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
      {children}
    </div>
  );
}

function OptionRow({
  label,
  active,
  effective,
  onSelect,
}: {
  label: string;
  active: boolean;
  effective?: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "flex w-full items-center justify-between rounded-sm px-2 py-1.5 text-left text-sm transition-colors hover:bg-muted",
        active ? "bg-muted text-foreground" : "text-muted-foreground",
      )}
    >
      <span className="flex items-center gap-1.5">
        {label}
        {effective ? (
          <span className="rounded-sm bg-status-conforming/15 px-1 py-0.5 text-[10px] font-medium leading-none text-status-conforming">
            effective
          </span>
        ) : null}
      </span>
      {active ? <Check className="h-3.5 w-3.5" /> : null}
    </button>
  );
}

export function ContextSwitcher() {
  const [open, setOpen] = useState(false);
  const [projectKey, setProjectKey] = useState(PROJECT_OPTIONS[0].key);

  const project = useMemo(
    () => PROJECT_OPTIONS.find((p) => p.key === projectKey) ?? PROJECT_OPTIONS[0],
    [projectKey],
  );

  const [platformKey, setPlatformKey] = useState(project.platforms[0].key);
  const platform = useMemo(
    () => project.platforms.find((p) => p.key === platformKey) ?? project.platforms[0],
    [project, platformKey],
  );

  const [versionKey, setVersionKey] = useState(
    platform.versions.find((v) => v.effective)?.key ?? platform.versions[0].key,
  );
  const version = useMemo(
    () => platform.versions.find((v) => v.key === versionKey) ?? platform.versions[0],
    [platform, versionKey],
  );

  function selectProject(key: string) {
    const next = PROJECT_OPTIONS.find((p) => p.key === key);
    if (!next) return;
    setProjectKey(key);
    setPlatformKey(next.platforms[0].key);
    setVersionKey(next.platforms[0].versions.find((v) => v.effective)?.key ?? next.platforms[0].versions[0].key);
  }

  function selectPlatform(key: string) {
    const next = project.platforms.find((p) => p.key === key);
    if (!next) return;
    setPlatformKey(key);
    setVersionKey(next.versions.find((v) => v.effective)?.key ?? next.versions[0].key);
  }

  function selectVersion(key: string) {
    setVersionKey(key);
    setOpen(false);
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-foreground outline-none transition-colors hover:bg-muted focus-visible:ring-1 focus-visible:ring-ring">
        <span>{project.label}</span>
        <span className="text-muted-foreground">/</span>
        <span>{platform.label}</span>
        <span className="text-muted-foreground">/</span>
        <span>{version.label}</span>
        <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
      </PopoverTrigger>
      <PopoverContent className="w-[28rem]">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <ColumnHeading>Project</ColumnHeading>
            <div className="flex flex-col gap-0.5">
              {PROJECT_OPTIONS.map((p) => (
                <OptionRow
                  key={p.key}
                  label={p.label}
                  active={p.key === project.key}
                  onSelect={() => selectProject(p.key)}
                />
              ))}
            </div>
          </div>
          <div>
            <ColumnHeading>Platform</ColumnHeading>
            <div className="flex flex-col gap-0.5">
              {project.platforms.map((p) => (
                <OptionRow
                  key={p.key}
                  label={p.label}
                  active={p.key === platform.key}
                  onSelect={() => selectPlatform(p.key)}
                />
              ))}
            </div>
          </div>
          <div>
            <ColumnHeading>Version</ColumnHeading>
            <div className="flex flex-col gap-0.5">
              {platform.versions.map((v) => (
                <OptionRow
                  key={v.key}
                  label={v.label}
                  active={v.key === version.key}
                  effective={v.effective}
                  onSelect={() => selectVersion(v.key)}
                />
              ))}
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
