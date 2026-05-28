import { Chip } from '@/components/ui/chip';
import type { Severity } from '@/features/upload-report/types';

const TONE: Record<Severity, 'success' | 'warning' | 'danger'> = {
  LOW: 'success',
  MEDIUM: 'warning',
  HIGH: 'danger',
};

const LABEL: Record<Severity, string> = {
  LOW: 'Low severity',
  MEDIUM: 'Medium severity',
  HIGH: 'High severity',
};

interface SeverityBadgeProps {
  severity: Severity | null | undefined;
  /**
   * Visual size hint. The new Chip primitive renders a single size, so this
   * prop is accepted (and ignored) only for backwards compatibility with
   * existing callers like the map report sheet.
   */
  size?: 'sm' | 'md';
}

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  if (!severity) return null;
  return <Chip label={LABEL[severity]} tone={TONE[severity]} />;
}
