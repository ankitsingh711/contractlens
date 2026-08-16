import { NextResponse } from "next/server";

// Minimal liveness probe for the Next.js standalone server. The standalone
// output has no built-in health route, and hitting "/" for a healthcheck
// would trigger a full page render (including any server-side data
// fetching) on every probe interval — this route is process-local and cheap.
export function GET() {
  return NextResponse.json({ status: "ok" });
}
