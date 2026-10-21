import type { Metadata } from "next";
import { connection } from "next/server";
import { Suspense } from "react";

import { ChatPanel } from "@/components/chat/chat-panel";
import { PageHeader } from "@/components/common/page-header";
import { SampleBadge } from "@/components/common/sample-badge";
import { Loading } from "@/components/common/states";
import { attempt, getApi, showSampleNotice } from "@/lib/api";

export const metadata: Metadata = {
  title: "Chat del auditor",
  description: "Haz preguntas abiertas sobre proyectos, el índice y la metodología.",
  robots: { index: false },
};

const BASE_SUGGESTIONS = [
  "¿Qué significa la confianza del índice?",
  "¿Qué es el NDVI?",
  "¿Bosque Vivo acusa a alguien de fraude?",
];

export default function ChatPage({ searchParams }: PageProps<"/chat">) {
  return (
    <>
      <PageHeader eyebrow="Auditor" title="Chat del auditor">
        Preguntas abiertas en texto libre. El agente consulta las auditorías, las series y la base de
        conocimiento, y muestra las evidencias que usó.
      </PageHeader>
      <Suspense fallback={<Loading label="Preparando el chat…" />}>
        <ChatLoader searchParams={searchParams} />
      </Suspense>
    </>
  );
}

async function ChatLoader({ searchParams }: Pick<PageProps<"/chat">, "searchParams">) {
  await connection();
  const { proyecto } = await searchParams;
  const projectId = Number(Array.isArray(proyecto) ? proyecto[0] : proyecto);

  const [projectResult, listResult] = await Promise.all([
    Number.isInteger(projectId) && projectId > 0 ? attempt(() => getApi().getProject(projectId)) : null,
    attempt(() => getApi().listProjects()),
  ]);

  const project = projectResult?.ok ? projectResult.data : null;
  const names = listResult.ok ? listResult.data.slice(0, 2).map((item) => item.name) : [];
  const suggestions = [
    ...names.map((name) => `¿Cómo está ${name}?`),
    ...(names.length === 2 ? [`Compara ${names[0]} con ${names[1]}`] : []),
    ...BASE_SUGGESTIONS,
  ];

  return (
    <>
      {showSampleNotice() && (
        <div className="mx-auto mb-4 max-w-3xl px-5">
          <SampleBadge />
        </div>
      )}
      <ChatPanel
        suggestions={suggestions}
        initialPrompt={project ? `Explícame el resultado de ${project.name}: ¿qué dice el índice y qué tan segura es la conclusión?` : undefined}
      />
    </>
  );
}
