const CITATION_MARKER_RE = /\[(\d+)\]/g;

export function FormattedAnswer({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  CITATION_MARKER_RE.lastIndex = 0;
  while ((match = CITATION_MARKER_RE.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    parts.push(
      <sup
        key={`${match.index}-${match[1]}`}
        className="ml-0.5 rounded bg-primary/10 px-1 text-[10px] font-semibold text-primary"
      >
        {match[1]}
      </sup>
    );
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return <p className="whitespace-pre-wrap text-sm leading-relaxed">{parts}</p>;
}
