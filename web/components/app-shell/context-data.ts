// Mock project/platform/version hierarchy until Setup is wired to a real backend.
export interface VersionOption {
  key: string;
  label: string;
  effective?: boolean;
}

export interface PlatformOption {
  key: string;
  label: string;
  versions: VersionOption[];
}

export interface ProjectOption {
  key: string;
  label: string;
  platforms: PlatformOption[];
}

export const PROJECT_OPTIONS: ProjectOption[] = [
  {
    key: "aeroflow-atm",
    label: "AeroFlow ATM",
    platforms: [
      {
        key: "primary-site",
        label: "Primary Site",
        versions: [
          { key: "5.2.0", label: "5.2.0", effective: true },
          { key: "5.1.4", label: "5.1.4" },
          { key: "5.0.9", label: "5.0.9" },
        ],
      },
      {
        key: "backup-site",
        label: "Backup Site",
        versions: [
          { key: "4.8.1", label: "4.8.1", effective: true },
          { key: "4.7.6", label: "4.7.6" },
        ],
      },
      {
        key: "simulator",
        label: "Simulator",
        versions: [
          { key: "6.0.0", label: "6.0.0", effective: true },
          { key: "5.9.3", label: "5.9.3" },
        ],
      },
    ],
  },
];
