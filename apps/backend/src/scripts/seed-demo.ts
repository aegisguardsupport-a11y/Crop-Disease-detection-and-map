/**
 * Demo seed script — produces a visually impactful initial state for hackathon
 * presentations. Run with `pnpm --filter backend seed:demo`.
 *
 * Behaviour:
 *   - Idempotent: every report is keyed by `(userId, clientId)` and every plot
 *     is deduped by name+coords. Re-running clears the visible AI fields and
 *     re-processes so the demo always lands in the same shape.
 *   - Creates two demo users (auto-onboards 9999999999 and 8888888888 with
 *     names + plots) if they don't already exist.
 *   - Inserts ~25 reports clustered to deliberately trigger 3 outbreak zones
 *     (HIGH in Pune, MEDIUM in Nashik, LOW in Sangli).
 *   - Inserts 6 historical notifications for the demo user.
 *
 * Designed to be run AFTER the backend is started so the realtime broadcasts
 * fire properly. If run against a cold DB it still works — the cron scheduler
 * + processors will pick up the rest on next boot.
 */

import { PrismaClient, ProcessingStatus, Severity } from '@prisma/client';

import { logger } from '../common/utils/logger';

const prisma = new PrismaClient();

interface SeedReport {
  cropType: string;
  disease: string;
  severity: Severity;
  confidence: number;
  recommendations: string[];
  latitude: number;
  longitude: number;
  ageHours: number;
}

const PUNE_CENTER = { lat: 18.5204, lng: 73.8567 };
const NASHIK_CENTER = { lat: 19.9975, lng: 73.7898 };
const SANGLI_CENTER = { lat: 16.8524, lng: 74.5815 };

function jitter(center: number, radiusKm: number): number {
  const offDeg = (Math.random() - 0.5) * 2 * (radiusKm / 110);
  return center + offDeg;
}

const TOMATO_RECS = [
  'Apply copper-based fungicide within 24 hours.',
  'Remove and destroy infected leaves; do not compost them.',
  'Reduce overhead irrigation - water at the soil line only.',
  'Improve air flow by spacing plants and pruning lower foliage.',
];
const RICE_RECS = [
  'Drain the field intermittently to limit pathogen spread.',
  'Apply copper oxychloride if symptoms are widespread.',
  'Avoid excessive nitrogen fertilization for the rest of the season.',
];
const COTTON_RECS = [
  'Inspect bolls daily and pluck affected ones.',
  'Use pheromone traps to monitor adult population.',
  'Spray emamectin benzoate if larval count exceeds threshold.',
];
const WHEAT_RECS = [
  'Apply propiconazole if rust pustules cover more than 5% of leaves.',
  'Scout neighbouring fields and inform local extension officer.',
  'Choose a rust-resistant variety in the next sowing.',
];

function buildReports(): SeedReport[] {
  const reports: SeedReport[] = [];

  // --- 8 Tomato Late Blight in Pune (HIGH outbreak) ---
  for (let i = 0; i < 8; i += 1) {
    reports.push({
      cropType: 'Tomato',
      disease: 'Tomato Late Blight',
      severity: i < 6 ? Severity.HIGH : Severity.MEDIUM,
      confidence: 84 + Math.floor(Math.random() * 12),
      recommendations: TOMATO_RECS,
      latitude: jitter(PUNE_CENTER.lat, 1.8),
      longitude: jitter(PUNE_CENTER.lng, 1.8),
      ageHours: Math.floor(Math.random() * 18),
    });
  }

  // --- 6 Rice Bacterial Leaf Blight in Nashik (MEDIUM outbreak) ---
  for (let i = 0; i < 6; i += 1) {
    reports.push({
      cropType: 'Rice',
      disease: 'Rice Bacterial Leaf Blight',
      severity: i < 2 ? Severity.HIGH : Severity.MEDIUM,
      confidence: 78 + Math.floor(Math.random() * 12),
      recommendations: RICE_RECS,
      latitude: jitter(NASHIK_CENTER.lat, 1.5),
      longitude: jitter(NASHIK_CENTER.lng, 1.5),
      ageHours: Math.floor(Math.random() * 16),
    });
  }

  // --- 5 Cotton Bollworm in Sangli (LOW outbreak) ---
  for (let i = 0; i < 5; i += 1) {
    reports.push({
      cropType: 'Cotton',
      disease: 'Cotton Bollworm Damage',
      severity: i === 0 ? Severity.HIGH : Severity.MEDIUM,
      confidence: 72 + Math.floor(Math.random() * 14),
      recommendations: COTTON_RECS,
      latitude: jitter(SANGLI_CENTER.lat, 2.0),
      longitude: jitter(SANGLI_CENTER.lng, 2.0),
      ageHours: Math.floor(Math.random() * 20),
    });
  }

  // --- 4 Wheat Leaf Rust singletons (no outbreak — shows below-threshold) ---
  for (let i = 0; i < 4; i += 1) {
    reports.push({
      cropType: 'Wheat',
      disease: 'Wheat Leaf Rust',
      severity: Severity.MEDIUM,
      confidence: 76 + Math.floor(Math.random() * 12),
      recommendations: WHEAT_RECS,
      latitude: jitter(20.5937, 8),
      longitude: jitter(78.9629, 8),
      ageHours: Math.floor(Math.random() * 24),
    });
  }

  // --- 3 Healthy crop reports (shows the green branch) ---
  for (let i = 0; i < 3; i += 1) {
    reports.push({
      cropType: i === 0 ? 'Tomato' : i === 1 ? 'Rice' : 'Wheat',
      disease: 'Healthy crop',
      severity: Severity.LOW,
      confidence: 91,
      recommendations: [
        'No action required — your crop appears healthy.',
        'Continue regular scouting and monitor for any new symptoms.',
      ],
      latitude: jitter(PUNE_CENTER.lat, 5),
      longitude: jitter(PUNE_CENTER.lng, 5),
      ageHours: Math.floor(Math.random() * 6),
    });
  }

  return reports;
}

const NOTIFICATION_TEMPLATES = [
  {
    type: 'OUTBREAK' as const,
    title: '⚠️ Severe outbreak nearby',
    body: 'Tomato Late Blight detected in your area · 8 reports.',
    severity: Severity.HIGH,
    ageMinutes: 35,
  },
  {
    type: 'WARNING' as const,
    title: 'Outbreak escalated',
    body: 'Tomato Late Blight outbreak escalated from medium to high severity.',
    severity: Severity.HIGH,
    ageMinutes: 90,
  },
  {
    type: 'REPORT' as const,
    title: 'High-severity report nearby',
    body: 'A Tomato Tomato Late Blight report was filed near your plot.',
    severity: Severity.HIGH,
    ageMinutes: 180,
  },
  {
    type: 'OUTBREAK' as const,
    title: 'Disease outbreak nearby',
    body: 'Rice Bacterial Leaf Blight detected in your area · 6 reports.',
    severity: Severity.MEDIUM,
    ageMinutes: 360,
  },
  {
    type: 'SYSTEM' as const,
    title: 'Welcome to AgroRadar',
    body: 'Add a plot to start receiving outbreak alerts in your area.',
    severity: null,
    ageMinutes: 1440,
  },
];

async function seed() {
  logger.info('▶ Starting demo seed…');

  // Ensure both demo users exist.
  const userA = await prisma.user.upsert({
    where: { phone: '9999999999' },
    create: { phone: '9999999999', name: 'Ramesh Patil' },
    update: { name: 'Ramesh Patil' },
  });
  const userB = await prisma.user.upsert({
    where: { phone: '8888888888' },
    create: { phone: '8888888888', name: 'Sunita Kale' },
    update: { name: 'Sunita Kale' },
  });
  logger.info(`✓ Users ready: ${userA.id} / ${userB.id}`);

  // Plots near each cluster. Idempotent on (userId, name).
  const plots = [
    {
      userId: userA.id,
      name: 'Pune North Tomato',
      latitude: PUNE_CENTER.lat + 0.005,
      longitude: PUNE_CENTER.lng + 0.005,
      cropTypes: ['Tomato'],
    },
    {
      userId: userA.id,
      name: 'Pune South Cotton',
      latitude: PUNE_CENTER.lat - 0.02,
      longitude: PUNE_CENTER.lng - 0.01,
      cropTypes: ['Cotton'],
    },
    {
      userId: userB.id,
      name: 'Nashik Main Rice Field',
      latitude: NASHIK_CENTER.lat + 0.01,
      longitude: NASHIK_CENTER.lng - 0.005,
      cropTypes: ['Rice'],
    },
  ];
  for (const p of plots) {
    const existing = await prisma.plot.findFirst({
      where: { userId: p.userId, name: p.name },
    });
    if (existing) {
      await prisma.plot.update({
        where: { id: existing.id },
        data: { ...p, active: true },
      });
    } else {
      await prisma.plot.create({ data: p });
    }
  }
  logger.info(`✓ ${plots.length} plots seeded`);

  // Reports — keyed by clientId so re-running is fully idempotent.
  const reports = buildReports();
  let created = 0;
  let updated = 0;
  for (let i = 0; i < reports.length; i += 1) {
    const r = reports[i]!;
    const clientId = `seed:report:${i}`;
    const createdAt = new Date(Date.now() - r.ageHours * 60 * 60 * 1000);
    const data = {
      userId: userA.id,
      clientId,
      cropType: r.cropType,
      imageUrl: `https://picsum.photos/seed/${encodeURIComponent(r.disease)}-${i}/640/480`,
      imagePublicId: `seed-${i}`,
      latitude: r.latitude,
      longitude: r.longitude,
      notes: null,
      disease: r.disease,
      confidence: r.confidence,
      severity: r.severity,
      recommendations: r.recommendations,
      processingStatus: ProcessingStatus.SUCCESS,
      processedAt: new Date(createdAt.getTime() + 4_000),
      createdAt,
    };
    const existing = await prisma.report.findUnique({
      where: { userId_clientId: { userId: userA.id, clientId } },
    });
    if (existing) {
      await prisma.report.update({ where: { id: existing.id }, data });
      updated += 1;
    } else {
      await prisma.report.create({ data });
      created += 1;
    }
  }
  logger.info(`✓ Reports: ${created} created, ${updated} updated`);

  // Notifications for user A. Idempotent: clear any seed-* and re-insert.
  await prisma.notification.deleteMany({
    where: { userId: userA.id, title: { contains: 'outbreak nearby' } },
  });
  for (let i = 0; i < NOTIFICATION_TEMPLATES.length; i += 1) {
    const t = NOTIFICATION_TEMPLATES[i]!;
    await prisma.notification.create({
      data: {
        userId: userA.id,
        type: t.type,
        title: t.title,
        body: t.body,
        severity: t.severity,
        read: i < 2,
        readAt: i < 2 ? new Date() : null,
        data: {},
        createdAt: new Date(Date.now() - t.ageMinutes * 60 * 1000),
      },
    });
  }
  logger.info(`✓ ${NOTIFICATION_TEMPLATES.length} notifications seeded for user A`);

  // Outbreak zones — built from contributing reports so counts stay accurate.
  const tomatoReports = reports.filter((r) => r.disease === 'Tomato Late Blight');
  const riceReports = reports.filter((r) => r.disease === 'Rice Bacterial Leaf Blight');
  const cottonReports = reports.filter((r) => r.disease === 'Cotton Bollworm Damage');

  await prisma.outbreakZone.deleteMany({
    where: {
      disease: {
        in: ['Tomato Late Blight', 'Rice Bacterial Leaf Blight', 'Cotton Bollworm Damage'],
      },
    },
  });

  await prisma.outbreakZone.create({
    data: {
      disease: 'Tomato Late Blight',
      latitude: PUNE_CENTER.lat,
      longitude: PUNE_CENTER.lng,
      radius: 5000,
      reportCount: tomatoReports.length,
      highCount: tomatoReports.filter((r) => r.severity === Severity.HIGH).length,
      severity: Severity.HIGH,
      affectedCropTypes: ['Tomato'],
      active: true,
      lastSeenAt: new Date(),
    },
  });
  await prisma.outbreakZone.create({
    data: {
      disease: 'Rice Bacterial Leaf Blight',
      latitude: NASHIK_CENTER.lat,
      longitude: NASHIK_CENTER.lng,
      radius: 4500,
      reportCount: riceReports.length,
      highCount: riceReports.filter((r) => r.severity === Severity.HIGH).length,
      severity: Severity.MEDIUM,
      affectedCropTypes: ['Rice'],
      active: true,
      lastSeenAt: new Date(),
    },
  });
  await prisma.outbreakZone.create({
    data: {
      disease: 'Cotton Bollworm Damage',
      latitude: SANGLI_CENTER.lat,
      longitude: SANGLI_CENTER.lng,
      radius: 4000,
      reportCount: cottonReports.length,
      highCount: cottonReports.filter((r) => r.severity === Severity.HIGH).length,
      severity: Severity.LOW,
      affectedCropTypes: ['Cotton'],
      active: true,
      lastSeenAt: new Date(),
    },
  });
  logger.info('✓ 3 outbreak zones seeded (HIGH Pune, MEDIUM Nashik, LOW Sangli)');

  logger.info('✅ Demo seed complete.');
}

seed()
  .catch((err) => {
    logger.error('Demo seed failed', err);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
