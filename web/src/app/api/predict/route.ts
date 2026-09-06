import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { promisify } from "node:util";

export const runtime = "nodejs";

const execFileAsync = promisify(execFile);
const allowedTargets = new Set(["전체 연령", "65세 이상"]);
const allowedCities = new Set(["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "수원", "춘천", "청주", "전주", "목포", "안동", "창원", "제주"]);

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const target = String(body.target ?? "");
    const date = String(body.date ?? "");
    const city = String(body.city ?? "");
    const startHour = Number(body.startHour);
    const durationMinutes = Number(body.durationMinutes);

    if (!allowedTargets.has(target) || !allowedCities.has(city)) {
      return Response.json({ message: "예측 대상 또는 지역이 올바르지 않습니다." }, { status: 400 });
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !Number.isInteger(startHour) || startHour < 0 || startHour > 23) {
      return Response.json({ message: "날짜 또는 외출 시각을 확인해 주세요." }, { status: 400 });
    }
    if (!Number.isInteger(durationMinutes) || durationMinutes < 0 || durationMinutes > 1440) {
      return Response.json({ message: "체류시간은 0~1440분 사이여야 합니다." }, { status: 400 });
    }

    const projectRoot = path.resolve(process.cwd(), "..");
    const windowsPython = path.join(projectRoot, ".venv", "Scripts", "python.exe");
    const unixPython = path.join(projectRoot, ".venv", "bin", "python");
    const python = existsSync(windowsPython) ? windowsPython : existsSync(unixPython) ? unixPython : "python";
    const script = path.join(projectRoot, "web", "scripts", "predict.py");

    const { stdout } = await execFileAsync(
      python,
      [script, "--target", target, "--date", date, "--city", city, "--start-hour", String(startHour), "--duration", String(durationMinutes)],
      {
        cwd: projectRoot,
        encoding: "utf8",
        timeout: 180_000,
        maxBuffer: 1024 * 1024,
        env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      },
    );

    return Response.json(JSON.parse(stdout));
  } catch (error) {
    const detail = error instanceof Error ? error.message : "알 수 없는 오류";
    console.error("Prediction failed:", detail);
    return Response.json({ message: "예측 정보를 불러오지 못했습니다. 날짜와 네트워크 상태를 확인해 주세요." }, { status: 500 });
  }
}
