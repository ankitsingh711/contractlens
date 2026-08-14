import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ComparisonRow, ComparisonSide } from "@/types/comparison";

function SideCell({ side }: { side: ComparisonSide }) {
  if (!side.found) {
    return <span className="text-xs text-muted-foreground italic">Not found</span>;
  }
  return (
    <div className="space-y-1">
      <p className="text-sm leading-snug">{side.text}</p>
      <p className="text-xs text-muted-foreground">
        {[side.section && `Section ${side.section}`, side.page && `Page ${side.page}`]
          .filter(Boolean)
          .join(" — ")}
      </p>
    </div>
  );
}

export function ComparisonTable({
  rows,
  labelA,
  labelB,
}: {
  rows: ComparisonRow[];
  labelA: string;
  labelB: string;
}) {
  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-40">Category</TableHead>
            <TableHead className="w-[38%]">{labelA}</TableHead>
            <TableHead className="w-[38%]">{labelB}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.category}>
              <TableCell className="align-top font-medium">{row.label}</TableCell>
              <TableCell className="align-top">
                <SideCell side={row.document_a} />
              </TableCell>
              <TableCell className="align-top">
                <SideCell side={row.document_b} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
