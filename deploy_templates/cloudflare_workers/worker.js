export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return Response.json({
        status: "ok",
        service: "MercadoLibre AutoDesign Cloudflare Gateway"
      });
    }

    if (url.pathname !== "/generate" || request.method !== "POST") {
      return Response.json(
        { status: "error", message: "Use POST /generate" },
        { status: 404 }
      );
    }

    const auth = request.headers.get("Authorization") || "";
    if (env.API_TOKEN && auth !== `Bearer ${env.API_TOKEN}`) {
      return Response.json(
        { status: "error", message: "Unauthorized" },
        { status: 401 }
      );
    }

    const upstream = `${env.GENERATOR_BASE_URL}/generate`;
    const response = await fetch(upstream, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: await request.text()
    });

    return new Response(await response.text(), {
      status: response.status,
      headers: { "Content-Type": "application/json; charset=utf-8" }
    });
  }
};
