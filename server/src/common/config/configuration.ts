import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

function getPromptsFile(): string | null {
  try {
    const currentDir = path.dirname(fileURLToPath(import.meta.url));
    const candidates = [
      path.resolve(process.cwd(), 'prompts.json'),
      path.resolve(process.cwd(), 'server', 'prompts.json'),
      path.resolve(currentDir, '../../../prompts.json'),
      path.resolve(currentDir, '../../../../prompts.json'),
    ];
    for (const p of candidates) {
      if (fs.existsSync(p)) return p;
    }
  } catch {
    const p = path.resolve(process.cwd(), 'prompts.json');
    if (fs.existsSync(p)) return p;
  }
  return null;
}

export function readPrompts(): Record<string, any> {
  const filePath = getPromptsFile();
  if (!filePath) return {};
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch (err) {
    console.error(`[config] Failed to parse ${filePath}:`, err);
    return {};
  }
}

export default () => {
  const prompts = readPrompts();
  return {
    gemini: {
      apiKey: process.env.GEMINI_API_KEY,
      apiUrl:
        process.env.GEMINI_API_URL ||
        'https://generativelanguage.googleapis.com/v1beta',
      model: process.env.GEMINI_MODEL || 'gemini-flash-latest',
      translatePrompt:
        process.env.GEMINI_TRANSLATE_PROMPT ||
        prompts.translate?.prompt ||
        'Translate the following texts to {target_lang}. Return ONLY valid JSON with a "results" array.',
      keepMemesTranslateSuffix:
        process.env.GEMINI_TRANSLATE_KEEP_MEMES_SUFFIX ||
        prompts.translate?.keep_memes_suffix ||
        ' IMPORTANT: If a line is a globally famous quote, meme, crowd noise, screaming, or a short untranslatable exclamation (e.g., "Ah shit", "Yo!", "Wow!", "Ahhh!"), DO NOT translate it. Leave it EXACTLY in its original English text.',
      adaptPrompt:
        process.env.GEMINI_ADAPT_PROMPT ||
        prompts.adapt?.prompt ||
        'Rewrite each line for a Russian TTS dubbing script. Keep natural flow, match timing and emotion.',
      keepMemesAdaptSuffix:
        process.env.GEMINI_ADAPT_KEEP_MEMES_SUFFIX ||
        prompts.adapt?.keep_memes_suffix ||
        ' If a line is an English meme/quote (e.g. "Ah shit, here we go again"), leave it EXACTLY in English, do not translate or transliterate it. For all other lines, keep them in Russian.',
    },
    groq: {
      apiKey: process.env.GROQ_API_KEY,
      apiUrl:
        process.env.GROQ_API_URL ||
        'https://api.groq.com/openai/v1/audio/transcriptions',
      model: process.env.GROQ_MODEL || 'whisper-large-v3-turbo',
    },
    fishAudio: {
      apiKey: process.env.FISH_AUDIO_API_KEY,
      apiUrl: process.env.FISH_AUDIO_API_URL || 'https://api.fish.audio/v1/tts',
      model: process.env.FISH_AUDIO_MODEL || 'tts-1',
    },
  };
};
