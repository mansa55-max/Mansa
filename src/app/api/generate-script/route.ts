import { NextResponse } from "next/server";
import { generateUgcScript } from "@/lib/script-generator";
import type { Tone } from "@/lib/types";

export async function POST(request: Request) {
  const body = await request.json();
  const productName = String(body.productName ?? "").trim();
  const productDescription = String(body.productDescription ?? "").trim();
  const tone = (body.tone as Tone) ?? "excited";

  if (!productName) {
    return NextResponse.json({ error: "productName is required" }, { status: 400 });
  }

  const script = generateUgcScript({ productName, productDescription, tone });
  return NextResponse.json({ script });
}
