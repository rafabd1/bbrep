import { readdir } from "node:fs/promises";
import path from "node:path";

export const qualityScores = {
  excellent: 5,
  good: 4,
  average: 3,
  poor: 1,
  none: 1,
  ghosted: 1,
  slow: 2,
  medium: 3,
  fast: 5,
  unpaid: 1,
  "not-applicable": null,
  unknown: null,
};

export const problemTags = {
  cvssmagic: { emoji: "\u{1F3A9}", label: "CVSS magic" },
  scam: { emoji: "\u{1F480}", label: "scam" },
  ghosting: { emoji: "\u{1F47B}", label: "ghosting" },
  lowball: { emoji: "\u{1FA99}", label: "lowball" },
  slowpay: { emoji: "\u{1F570}\uFE0F", label: "slow pay" },
  scopechaos: { emoji: "\u{1F9E8}", label: "scope chaos" },
  wontfix: { emoji: "\u{1F6D1}", label: "wontfix loop" },
};

const problemTagAliases = {
  "cvss-magic": "cvssmagic",
  ghosted: "ghosting",
  "slow-pay": "slowpay",
  "scope-chaos": "scopechaos",
  scopebait: "scopechaos",
  "wont-fix": "wontfix",
  wontfixloop: "wontfix",
};

const hashTagPattern = /#([a-z0-9][a-z0-9-]*)/gi;

function normalizeProblemTag(tag) {
  const normalized = String(tag ?? "")
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-{2,}/g, "-");
  return problemTagAliases[normalized] ?? normalized;
}

function reviewProblemTags(review) {
  const tags = Array.isArray(review.tags) ? review.tags : [];
  const noteTags = [...String(review.note ?? "").matchAll(hashTagPattern)].map((match) => match[1]);
  const unique = new Set([...tags, ...noteTags].map(normalizeProblemTag));
  return [...unique]
    .filter((tag) => Object.hasOwn(problemTags, tag))
    .map((tag) => ({
      key: tag,
      ...problemTags[tag],
    }));
}

function noteParts(note) {
  const text = String(note ?? "");
  const parts = [];
  let index = 0;

  for (const match of text.matchAll(hashTagPattern)) {
    if (match.index > index) {
      parts.push({ type: "text", value: text.slice(index, match.index) });
    }

    const tag = normalizeProblemTag(match[1]);
    if (Object.hasOwn(problemTags, tag)) {
      parts.push({
        type: "tag",
        value: match[0],
        key: tag,
        emoji: problemTags[tag].emoji,
        label: problemTags[tag].label,
      });
    } else {
      parts.push({ type: "text", value: match[0] });
    }
    index = match.index + match[0].length;
  }

  if (index < text.length) {
    parts.push({ type: "text", value: text.slice(index) });
  }

  return parts;
}

export async function globPrograms(root) {
  const dataRoot = path.join(root, "data", "programs");
  let platforms = [];

  try {
    platforms = await readdir(dataRoot, { withFileTypes: true });
  } catch {
    return [];
  }

  const files = [];
  for (const platform of platforms) {
    if (!platform.isDirectory()) continue;
    const platformDir = path.join(dataRoot, platform.name);
    const entries = await readdir(platformDir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isFile() && [".yml", ".yaml"].includes(path.extname(entry.name))) {
        files.push(path.join(platformDir, entry.name));
      }
    }
  }

  return files.sort();
}

export function normalizeProgram(record, filePath, root) {
  const program = record.program;
  const reviews = record.reviews ?? [];
  const enrichedReviews = reviews
    .map((review) => {
      const knownProblemTags = reviewProblemTags(review);
      return {
        ...review,
        problemTags: knownProblemTags,
        noteParts: noteParts(review.note),
        reviewerLabel:
          review.reviewer?.display === "anonymous" ? "anonymous" : `@${review.reviewer.github}`,
      };
    })
    .sort((a, b) => String(b.submitted_at).localeCompare(String(a.submitted_at)));

  const reviewCount = enrichedReviews.length;
  const averageRating =
    reviewCount === 0
      ? 0
      : Number(
          (
            enrichedReviews.reduce((sum, review) => sum + Number(review.rating ?? 0), 0) /
            reviewCount
          ).toFixed(2),
        );

  const latestReview = enrichedReviews[0]?.submitted_at ?? null;
  const scoreFields = [
    "response_time",
    "triage_quality",
    "payment_reliability",
    "scope_accuracy",
    "communication",
  ];

  const signals = Object.fromEntries(
    scoreFields.map((field) => {
      const values = enrichedReviews
        .map((review) => qualityScores[review[field]])
        .filter((value) => typeof value === "number");
      const avg = values.length
        ? Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(2))
        : null;
      return [field, avg];
    }),
  );

  const problemStats = Object.entries(
    enrichedReviews
      .flatMap((review) => review.problemTags)
      .reduce((counts, tag) => {
        counts[tag.key] = (counts[tag.key] ?? 0) + 1;
        return counts;
      }, {}),
  )
    .map(([key, count]) => ({
      key,
      count,
      ...problemTags[key],
    }))
    .sort((a, b) => b.count - a.count || a.key.localeCompare(b.key));

  return {
    name: program.name,
    platform: program.platform,
    slug: program.slug,
    programUrl: program.program_url,
    policyUrl: program.policy_url ?? null,
    path: `/p/${program.platform}/${program.slug}`,
    sourcePath: path.relative(root, filePath).replaceAll("\\", "/"),
    reviewCount,
    averageRating,
    latestReview,
    signals,
    problemStats,
    reviews: enrichedReviews,
  };
}
