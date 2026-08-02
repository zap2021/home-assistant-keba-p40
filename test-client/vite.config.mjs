import { defineConfig } from "vite";
import { request as httpsRequest } from "node:https";

const jsonHeaders = {
  "content-type": "application/json; charset=utf-8",
};

function sendJson(res, statusCode, payload) {
  res.statusCode = statusCode;
  for (const [key, value] of Object.entries(jsonHeaders)) {
    res.setHeader(key, value);
  }
  res.end(JSON.stringify(payload, null, 2));
}

function getForwardUrl(req) {
  const target = req.headers["x-keba-target"];
  if (typeof target !== "string" || target.length === 0) {
    return null;
  }

  const path = req.url.replace(/^\/keba-api/, "") || "/";
  return new URL(path, target);
}

export default defineConfig({
  server: {
    port: 4174,
  },
  plugins: [
    {
      name: "keba-api-forwarder",
      configureServer(server) {
        server.middlewares.use("/keba-api", async (req, res) => {
          const url = getForwardUrl(req);
          if (!url) {
            sendJson(res, 400, { error: "Missing x-keba-target header" });
            return;
          }

          const allowInsecure = req.headers["x-keba-insecure"] === "true";
          const bodyChunks = [];

          req.on("data", (chunk) => bodyChunks.push(chunk));
          req.on("error", (error) => {
            sendJson(res, 500, { error: String(error) });
          });

          req.on("end", async () => {
            try {
              const upstreamResponse = await forwardRequest({
                url,
                method: req.method ?? "GET",
                headers: Object.fromEntries(
                  Object.entries(req.headers).filter(([key]) => !key.startsWith("x-keba-") && key !== "host"),
                ),
                body:
                  req.method === "GET" || req.method === "HEAD" || bodyChunks.length === 0
                    ? undefined
                    : Buffer.concat(bodyChunks),
                allowInsecure,
              });

              res.statusCode = upstreamResponse.statusCode;
              for (const [key, value] of Object.entries(upstreamResponse.headers)) {
                if (key.toLowerCase() !== "content-encoding" && value !== undefined) {
                  res.setHeader(key, value);
                }
              }

              res.end(upstreamResponse.body);
            } catch (error) {
              sendJson(res, 502, {
                error: error instanceof Error ? error.message : String(error),
                target: url.toString(),
              });
            }
          });
        });
      },
    },
  ],
});

function forwardRequest({ url, method, headers, body, allowInsecure }) {
  return new Promise((resolve, reject) => {
    const request = httpsRequest(
      url,
      {
        method,
        headers,
        rejectUnauthorized: !allowInsecure,
      },
      (response) => {
        const chunks = [];
        response.on("data", (chunk) => chunks.push(chunk));
        response.on("end", () => {
          resolve({
            statusCode: response.statusCode ?? 502,
            headers: response.headers,
            body: Buffer.concat(chunks),
          });
        });
      },
    );

    request.on("error", reject);

    if (body) {
      request.write(body);
    }

    request.end();
  });
}
