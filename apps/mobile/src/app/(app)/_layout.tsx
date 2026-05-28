import { Redirect, Tabs } from 'expo-router';
import { useEffect, useState } from 'react';

import { TabBar } from '@/components/navigation/tab-bar';
import { onboardingStorage } from '@/features/plots/onboarding-storage';
import { usePlots } from '@/features/plots/hooks/use-plots';
import { useAuthStore } from '@/store/auth.store';

export default function AppLayout() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isHydrated = useAuthStore((s) => s.isHydrated);
  const user = useAuthStore((s) => s.user);
  const { data: plots, isPending: plotsPending } = usePlots();

  const [skipped, setSkipped] = useState<boolean | null>(null);
  useEffect(() => {
    void onboardingStorage.getSkipped().then(setSkipped);
  }, []);

  if (!isHydrated) return null;
  if (!isAuthenticated) return <Redirect href="/login" />;
  if (skipped === null) return null;

  // First-time users (no name, no plots) get nudged through onboarding once.
  const needsOnboarding =
    !skipped && !user?.name && !plotsPending && (plots?.length ?? 0) === 0;
  if (needsOnboarding) return <Redirect href="/name" />;

  return (
    <Tabs
      tabBar={(props) => <TabBar {...props} />}
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: 'transparent' },
      }}
    >
      <Tabs.Screen name="index" options={{ title: 'Home' }} />
      <Tabs.Screen name="map" options={{ title: 'Map' }} />
      <Tabs.Screen name="upload" options={{ title: 'Report' }} />
      <Tabs.Screen name="notifications" options={{ title: 'Alerts' }} />
      <Tabs.Screen name="profile" options={{ title: 'Profile' }} />
    </Tabs>
  );
}
