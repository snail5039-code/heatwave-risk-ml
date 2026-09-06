import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { promisify } from "node:util";

export const runtime = "nodejs";
const execFileAsync = promisify(execFile);

export async function GET(request: Request) {
  const target = new URL(request.url).searchParams.get("target") ?? "전체 연령";
  if (target !== "전체 연령" && target !== "65세 이상") {
    return Response.json({ message: "예측 대상이 올바르지 않습니다." }, { status: 400 });
  }

  try {
    const projectRoot = path.resolve(process.cwd(), "..");
    const windowsPython = path.join(projectRoot, ".venv", "Scripts", "python.exe");
    const unixPython = path.join(projectRoot, ".venv", "bin", "python");
    const python = existsSync(windowsPython) ? windowsPython : existsSync(unixPython) ? unixPython : "python";
    const script = path.join(projectRoot, "web", "scripts", "analysis.py");
    const { stdout } = await execFileAsync(python, [script, "--target", target], {
      cwd: projectRoot,
      encoding: "utf8",
      timeout: 60_000,
      maxBuffer: 4 * 1024 * 1024,
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    });
    return Response.json(JSON.parse(stdout));
  } catch (error) {
    console.error("Analysis failed:", error);
    return Response.json({ message: "분석 자료를 불러오지 못했습니다." }, { status: 500 });
  }
}
