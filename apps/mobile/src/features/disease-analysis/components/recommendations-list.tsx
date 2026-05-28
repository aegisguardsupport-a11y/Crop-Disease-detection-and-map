import { RecommendationsCard } from '@/features/report-flow';

export function RecommendationsList({ items }: { items: string[] | null | undefined }) {
  return <RecommendationsCard items={items ?? []} />;
}
