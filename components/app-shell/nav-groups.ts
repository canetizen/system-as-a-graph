// `readiness` is hardcoded to `muted` until each group's backing pipeline stage is wired up.
export interface NavGroup {
  key: string;
  label: string;
  href: string;
  readiness: "muted" | "conforming";
}

export const NAV_GROUPS: NavGroup[] = [
  { key: "setup", label: "Setup", href: "/setup", readiness: "muted" },
  { key: "model", label: "Model", href: "/model", readiness: "muted" },
  {
    key: "analytical-data",
    label: "Analytical Data",
    href: "/analytical-data",
    readiness: "muted",
  },
  { key: "findings", label: "Findings", href: "/findings", readiness: "muted" },
];
