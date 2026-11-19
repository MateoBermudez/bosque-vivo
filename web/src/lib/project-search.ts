export interface PickerProject {
  id: number;
  name: string;
  country: string | null;
  area_ha: number | null;
}

export function normalizeText(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

export function filterProjects(projects: PickerProject[], query: string, limit = 8): PickerProject[] {
  const tokens = normalizeText(query).split(" ").filter(Boolean);
  const byName = [...projects].sort((a, b) => a.name.localeCompare(b.name, "es"));
  if (tokens.length === 0) return byName.slice(0, limit);
  const matches = byName.filter((project) => {
    const name = normalizeText(project.name);
    return tokens.every((token) => name.includes(token));
  });
  const startsWith = (project: PickerProject) => normalizeText(project.name).startsWith(tokens[0]!);
  return [...matches.filter(startsWith), ...matches.filter((project) => !startsWith(project))].slice(0, limit);
}
