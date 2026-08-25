export function normalizeProjectName(name: string): string {
  return name.trim();
}

export function getProjectNameError(name: string): string | null {
  const trimmed = normalizeProjectName(name);
  if (!trimmed) return "Enter a project name";
  if (trimmed === "." || trimmed === "..") {
    return "Project name cannot be . or ..";
  }
  const hasControlCharacter = Array.from(trimmed).some(
    (char) => char.charCodeAt(0) < 32,
  );
  if (
    hasControlCharacter ||
    /[\\/<>:"|?*]/.test(trimmed) ||
    /[\s.]$/.test(trimmed)
  ) {
    return "Project name contains characters Windows cannot use";
  }
  return null;
}
