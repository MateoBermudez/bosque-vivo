import { Fragment } from "react";

import { parseBlocks, type Inline } from "@/lib/rich-text";

function Inlines({ items }: { items: Inline[] }) {
  return (
    <>
      {items.map((item, index) => {
        switch (item.kind) {
          case "bold":
            return <strong key={index}>{item.value}</strong>;
          case "italic":
            return <em key={index}>{item.value}</em>;
          case "code":
            return (
              <code key={index} className="rounded bg-secondary px-1 py-0.5 font-mono text-[0.9em]">
                {item.value}
              </code>
            );
          default:
            return <Fragment key={index}>{item.value}</Fragment>;
        }
      })}
    </>
  );
}

export function RichText({ text }: { text: string }) {
  return (
    <div className="space-y-2">
      {parseBlocks(text).map((block, index) =>
        block.kind === "list" ? (
          <ul key={index} className="list-disc space-y-1 pl-5">
            {block.items.map((item, itemIndex) => (
              <li key={itemIndex}>
                <Inlines items={item} />
              </li>
            ))}
          </ul>
        ) : (
          <p key={index}>
            <Inlines items={block.content} />
          </p>
        ),
      )}
    </div>
  );
}
