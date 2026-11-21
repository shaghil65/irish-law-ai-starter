import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';
const backend = process.env.BACKEND_URL || 'http://backend:8000';
async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const url = new URL(request.url);
  const target = `${backend}/api/${path.map(encodeURIComponent).join('/')}${url.search}`;
  try {
    const response = await fetch(target, {
      method: request.method,
      headers: { 'content-type': request.headers.get('content-type') || 'application/json' },
      body: request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.text(),
      cache: 'no-store',
      signal: AbortSignal.timeout(120000),
    });
    return new NextResponse(response.body, { status: response.status, headers: { 'content-type': response.headers.get('content-type') || 'application/json' } });
  } catch { return NextResponse.json({detail:'Backend unavailable'}, {status:503}); }
}
export { proxy as GET, proxy as POST };
