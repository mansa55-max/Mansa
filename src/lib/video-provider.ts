export interface VideoGenerationInput {
  script: string;
  avatarId: string;
  voiceId: string;
}

export interface VideoGenerationResult {
  videoUrl: string;
}

export interface VideoProvider {
  name: string;
  generate(input: VideoGenerationInput): Promise<VideoGenerationResult>;
}

// Sample public domain clip used as a stand-in "rendered video" so the full
// create -> generate -> watch pipeline works with zero external API keys.
const SAMPLE_VIDEO_URL =
  "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4";

class MockVideoProvider implements VideoProvider {
  name = "mock";

  async generate(_input: VideoGenerationInput): Promise<VideoGenerationResult> {
    // Simulate render latency so the UI's "generating" state is exercised.
    await new Promise((resolve) => setTimeout(resolve, 1500));
    return { videoUrl: SAMPLE_VIDEO_URL };
  }
}

// Talking-avatar rendering via HeyGen (https://docs.heygen.com). Requires
// HEYGEN_API_KEY. This uses HeyGen's async v2 video generation endpoint and
// polls for completion — verify field names against current HeyGen docs
// before relying on this in production, as third-party APIs evolve.
class HeyGenVideoProvider implements VideoProvider {
  name = "heygen";

  private apiKey = process.env.HEYGEN_API_KEY;

  async generate(input: VideoGenerationInput): Promise<VideoGenerationResult> {
    if (!this.apiKey) {
      throw new Error("HEYGEN_API_KEY is not set");
    }

    const createRes = await fetch("https://api.heygen.com/v2/video/generate", {
      method: "POST",
      headers: {
        "X-Api-Key": this.apiKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        video_inputs: [
          {
            character: { type: "avatar", avatar_id: input.avatarId, avatar_style: "normal" },
            voice: { type: "text", input_text: input.script, voice_id: input.voiceId },
          },
        ],
        dimension: { width: 720, height: 1280 },
      }),
    });

    if (!createRes.ok) {
      throw new Error(`HeyGen generate request failed: ${createRes.status}`);
    }

    const { data } = (await createRes.json()) as { data: { video_id: string } };
    const videoId = data.video_id;

    for (let attempt = 0; attempt < 30; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, 5000));

      const statusRes = await fetch(
        `https://api.heygen.com/v1/video_status.get?video_id=${videoId}`,
        { headers: { "X-Api-Key": this.apiKey } },
      );
      const statusJson = (await statusRes.json()) as {
        data: { status: string; video_url?: string };
      };

      if (statusJson.data.status === "completed" && statusJson.data.video_url) {
        return { videoUrl: statusJson.data.video_url };
      }
      if (statusJson.data.status === "failed") {
        throw new Error("HeyGen video generation failed");
      }
    }

    throw new Error("Timed out waiting for HeyGen video generation");
  }
}

export function getVideoProvider(): VideoProvider {
  const provider = process.env.VIDEO_PROVIDER ?? "mock";
  switch (provider) {
    case "heygen":
      return new HeyGenVideoProvider();
    case "mock":
    default:
      return new MockVideoProvider();
  }
}
