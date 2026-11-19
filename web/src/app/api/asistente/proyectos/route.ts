import { NextResponse } from "next/server";

import { attempt, getApi, isDemoProject } from "@/lib/api";

export async function GET() {
  const result = await attempt(() => getApi().listProjects());
  if (!result.ok) {
    return NextResponse.json({ error: result.message }, { status: 502 });
  }
  const projects = result.data
    .filter((project) => !isDemoProject(project))
    .map((project) => ({
      id: project.id,
      name: project.name,
      country: project.country ?? null,
      area_ha: project.area_ha ?? null,
    }));
  return NextResponse.json(
    { projects },
    { headers: { "Cache-Control": "public, max-age=300, s-maxage=300" } },
  );
}
