import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  copyFileToProject: vi.fn(),
}));

vi.mock("@/lib/tauri/fs", () => ({
  copyFileToProject: mocks.copyFileToProject,
}));

import {
  buildReferenceFilesSection,
  importReferenceFiles,
} from "@/lib/project-attachments";

describe("project attachment helpers", () => {
  beforeEach(() => {
    mocks.copyFileToProject.mockReset();
  });

  it("imports PDFs without creating extracted text files", async () => {
    mocks.copyFileToProject.mockResolvedValueOnce("attachments/paper.pdf");

    const files = await importReferenceFiles("C:/project", [
      "C:/source/paper.pdf",
    ]);

    expect(mocks.copyFileToProject).toHaveBeenCalledWith(
      "C:/project",
      "C:/source/paper.pdf",
      "attachments/paper.pdf",
    );
    expect(files).toEqual([
      {
        relativePath: "attachments/paper.pdf",
      },
    ]);
  });

  it("builds a prompt section that keeps PDF references as PDFs", () => {
    const section = buildReferenceFilesSection([
      { relativePath: "attachments/paper.pdf" },
      { relativePath: "attachments/data.csv" },
    ]);

    expect(section).toContain("### Reference Files");
    expect(section).toContain("`attachments/paper.pdf` (PDF)");
    expect(section).toContain("`attachments/data.csv`");
    expect(section).not.toContain("extracted text");
    expect(section).not.toContain(".pdf.txt");
  });
});
