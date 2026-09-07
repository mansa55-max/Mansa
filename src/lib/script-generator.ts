import type { Tone } from "./types";

interface GenerateScriptInput {
  productName: string;
  productDescription: string;
  tone: Tone;
}

const HOOKS: Record<Tone, string[]> = {
  excited: [
    "Okay wait, I need to talk about {product} because I'm obsessed.",
    "I was NOT expecting {product} to be this good, ngl.",
  ],
  casual: [
    "So a few weeks ago I picked up {product}, and honestly?",
    "Quick one — I've been using {product} and wanted to share.",
  ],
  professional: [
    "I've spent the last month testing {product}, and here's what stood out.",
    "If you're evaluating options, here's why {product} made the cut for me.",
  ],
  funny: [
    "My bank account is mad at me for buying {product}, but my life is better.",
    "{product} walked so my old routine could crawl into the trash.",
  ],
};

const BODIES: Record<Tone, string[]> = {
  excited: [
    "{description} Seriously, the difference was noticeable within days.",
    "{description} I keep telling my friends about it because it just works.",
  ],
  casual: [
    "{description} Nothing fancy, it just does what it says.",
    "{description} Not sponsored (yet), just genuinely happy with it.",
  ],
  professional: [
    "{description} The quality-to-price ratio is hard to beat right now.",
    "{description} It solved a real problem without adding extra complexity.",
  ],
  funny: [
    "{description} 10/10, would probably buy again even if I didn't need it.",
    "{description} My only regret is not finding it sooner.",
  ],
};

const CTAS: Record<Tone, string[]> = {
  excited: ["Link's below, go grab yours before it sells out!", "Trust me on this one, go check it out!"],
  casual: ["I'll drop the link if you want to try it.", "Worth a look if that's your kind of thing."],
  professional: ["Learn more using the link in the description.", "Full details are linked below."],
  funny: ["Don't say I didn't warn you. Link below.", "Go on, treat yourself. Link's below."],
};

function pick<T>(arr: T[], seed: number): T {
  return arr[seed % arr.length];
}

export function generateUgcScript({
  productName,
  productDescription,
  tone,
}: GenerateScriptInput): string {
  const seed = productName.length + productDescription.length;
  const hook = pick(HOOKS[tone], seed).replaceAll("{product}", productName);
  const description =
    productDescription.trim() || `${productName} has genuinely earned a spot in my routine.`;
  const body = pick(BODIES[tone], seed + 1).replaceAll("{description}", description);
  const cta = pick(CTAS[tone], seed + 2);

  return [hook, body, cta].join(" ");
}
