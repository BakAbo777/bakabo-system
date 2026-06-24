/**
 * BKS Verse — Cloudflare Worker
 * Proxy pubblico tra Shopify/client e il server Hetzner privato.
 * Route: verse.bakabo.club/* → VERSE_ORIGIN/*
 *
 * Variabili d'ambiente (Workers > Settings > Variables):
 *   VERSE_ORIGIN     = http://<IP_HETZNER>:8001
 *   ADMIN_SECRET_KEY = stesso di VERSE_SECRET_KEY nel .env server
 */

const ALLOWED_ORIGINS = [
  'https://bakabo.club',
  'https://bakabo.myshopify.com',
  'https://www.bakabo.club',
];

const CORS_HEADERS = {
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, X-Admin-Key',
  'Access-Control-Max-Age': '86400',
};

function corsHeaders(origin) {
  const allowed = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return { ...CORS_HEADERS, 'Access-Control-Allow-Origin': allowed };
}

// Endpoint pubblici (no auth)
const PUBLIC_PATHS = [
  /^\/verse\/submit$/,
  /^\/verse\/status\/\d+$/,
  /^\/leaderboard\//,
  /^\/lineage\//,
  /^\/reel\/storyboard\/\d+$/,
  /^\/reel\/episodes$/,
  /^\/health$/,
];

// Endpoint admin (richiede X-Admin-Key)
const ADMIN_PATHS = [
  /^\/verse\/approve\/\d+$/,
  /^\/verse\/publish\/\d+$/,
  /^\/verse\/pending$/,
];

export default {
  async fetch(request, env) {
    const url     = new URL(request.url);
    const origin  = request.headers.get('Origin') || '';
    const path    = url.pathname;

    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    // Rate limiting base (IP-based, semplice)
    const ip = request.headers.get('CF-Connecting-IP') || '';
    const rateLimitKey = `rate:${ip}`;
    const count = (await env.VERSE_KV?.get(rateLimitKey)) || '0';
    if (parseInt(count) > 30) {
      return new Response(JSON.stringify({ error: 'rate_limit' }), {
        status: 429,
        headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
      });
    }
    await env.VERSE_KV?.put(rateLimitKey, String(parseInt(count) + 1), { expirationTtl: 60 });

    const isPublic = PUBLIC_PATHS.some(rx => rx.test(path));
    const isAdmin  = ADMIN_PATHS.some(rx => rx.test(path));

    if (!isPublic && !isAdmin) {
      return new Response(JSON.stringify({ error: 'not_found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
      });
    }

    // Forward alla origine — rimuove Host per evitare Cloudflare loopback detection
    const targetUrl     = env.VERSE_ORIGIN + path + url.search;
    const fwdHeaders    = new Headers(request.headers);
    fwdHeaders.delete('Host');
    const proxyReq  = new Request(targetUrl, {
      method:  request.method,
      headers: fwdHeaders,
      body:    request.method !== 'GET' ? request.body : undefined,
    });

    let response;
    try {
      response = await fetch(proxyReq);
    } catch (err) {
      return new Response(JSON.stringify({ error: 'upstream_unreachable', detail: String(err) }), {
        status: 502,
        headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
      });
    }

    const newHeaders = new Headers(response.headers);
    Object.entries(corsHeaders(origin)).forEach(([k, v]) => newHeaders.set(k, v));

    return new Response(response.body, {
      status:  response.status,
      headers: newHeaders,
    });
  },
};
