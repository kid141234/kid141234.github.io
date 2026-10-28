import http from "node:http";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("./dist/", import.meta.url));
const port = Number(process.env.PORT || 4173);
const types = {".html":"text/html; charset=utf-8", ".css":"text/css; charset=utf-8", ".js":"text/javascript; charset=utf-8", ".svg":"image/svg+xml", ".png":"image/png", ".jpg":"image/jpeg", ".jpeg":"image/jpeg", ".webp":"image/webp", ".pdf":"application/pdf", ".ico":"image/x-icon"};
const server = http.createServer(async (req, res) => {
  try {
    if (!["GET", "HEAD"].includes(req.method)) { res.writeHead(405, {Allow:"GET, HEAD"}); res.end(); return; }
    const pathname = decodeURIComponent(new URL(req.url, `http://127.0.0.1:${port}`).pathname);
    const file = path.resolve(root, `.${pathname === "/" ? "/index.html" : pathname}`);
    const relative = path.relative(root, file);
    if (relative.startsWith("..") || path.isAbsolute(relative)) { res.writeHead(403); res.end("Forbidden"); return; }
    if (!(await stat(file)).isFile()) throw new Error("Not a file");
    const body = await readFile(file);
    res.writeHead(200, {"Content-Type":types[path.extname(file)] || "application/octet-stream", "Cache-Control":"no-store", "X-Content-Type-Options":"nosniff"});
    res.end(req.method === "HEAD" ? undefined : body);
  } catch {
    res.writeHead(404, {"Content-Type":"text/plain; charset=utf-8"});
    res.end("页面或文件不存在。");
  }
});
server.on("error", error => { console.error(error.message); process.exitCode = 1; });
server.listen(port, "127.0.0.1", () => console.log(`Local: http://127.0.0.1:${port}`));
process.on("SIGINT", () => server.close());
process.on("SIGTERM", () => server.close());
