export const config = {
  path: '/api/*',
};

export default async function proxyApi(request) {
  const configuredBackendUrl = process.env.BACKEND_API_URL;
  if (!configuredBackendUrl) {
    return Response.json(
      { detail: 'The FastAPI backend is not configured. Set BACKEND_API_URL in Netlify.' },
      { status: 503 },
    );
  }

  const backendBase = new URL(configuredBackendUrl);
  const incomingUrl = new URL(request.url);
  const apiPath = incomingUrl.pathname.slice('/api'.length);
  const backendPath = backendBase.pathname.replace(/\/+$/, '');
  const targetUrl = new URL(
    `${backendPath}${apiPath}${incomingUrl.search}`,
    backendBase.origin,
  );
  const headers = new Headers(request.headers);
  ['host', 'connection', 'content-length', 'transfer-encoding'].forEach(header => headers.delete(header));

  const body = ['GET', 'HEAD'].includes(request.method) ? undefined : await request.arrayBuffer();
  const response = await fetch(targetUrl, {
    method: request.method,
    headers,
    body,
    redirect: 'manual',
  });
  const responseHeaders = new Headers(response.headers);
  ['content-encoding', 'content-length', 'transfer-encoding'].forEach(header => responseHeaders.delete(header));

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  });
}
