import { copyFileToProject } from "@/lib/tauri/fs";

export interface ImportedReferenceFile {
  relativePath: string;
}

function baseName(path: string): string {
  return path.split(/[/\\]/).pop() || path;
}

function isPdfPath(path: string): boolean {
  return path.toLowerCase().endsWith(".pdf");
}

export async function importReferenceFiles(
  projectRoot: string,
  sourcePaths: string[],
  targetFolder = "attachments",
): Promise<ImportedReferenceFile[]> {
  const imported: ImportedReferenceFile[] = [];

  for (const sourcePath of sourcePaths) {
    const targetName = `${targetFolder}/${baseName(sourcePath)}`;
    const relativePath = await copyFileToProject(
      projectRoot,
      sourcePath,
      targetName,
    );
    const reference: ImportedReferenceFile = { relativePath };
    imported.push(reference);
  }

  return imported;
}

export function buildReferenceFilesSection(
  references: ImportedReferenceFile[],
): string {
  if (references.length === 0) return "";

  const lines = references.map((reference) => {
    if (isPdfPath(reference.relativePath)) {
      return `- \`${reference.relativePath}\` (PDF)`;
    }
    return `- \`${reference.relativePath}\``;
  });

  return [
    "",
    "### Reference Files",
    lines.join("\n"),
    "",
    "Please review them and incorporate relevant information.",
    "",
  ].join("\n");
}
