import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, Switch, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Bell, Moon, Sun, ChevronRight, Monitor, Activity, TestTube } from 'lucide-react-native';
import { useTheme, ThemeMode } from '../contexts/ThemeContext';

interface SettingItemProps {
  icon: any;
  title: string;
  subtitle?: string;
  onPress?: () => void;
  rightElement?: React.ReactNode;
  showChevron?: boolean;
  theme: {
    cardBackground: string;
    border: string;
    text: string;
    textSecondary: string;
  };
}

const SettingItem: React.FC<SettingItemProps> = ({
  icon: Icon,
  title,
  subtitle,
  onPress,
  rightElement,
  showChevron = false,
  theme,
}) => (
  <TouchableOpacity
    style={[
      styles.settingItem,
      {
        backgroundColor: theme.cardBackground,
        borderBottomColor: theme.border,
      },
    ]}
    onPress={onPress}
    disabled={!onPress}
  >
    <View style={styles.iconContainer}>
      <Icon size={24} color={theme.text} />
    </View>
    <View style={styles.contentContainer}>
      <Text style={[styles.settingTitle, { color: theme.text }]}>{title}</Text>
      {subtitle && (
        <Text style={[styles.settingSubtitle, { color: theme.textSecondary }]}>{subtitle}</Text>
      )}
    </View>
    <View style={styles.rightContainer}>
      {rightElement}
      {showChevron && <ChevronRight size={20} color={theme.textSecondary} />}
    </View>
  </TouchableOpacity>
);

export default function SettingsScreen({ navigation }: { navigation: any }) {
  const { theme, themeMode, setThemeMode } = useTheme();
  const [notificationsEnabled, setNotificationsEnabled] = React.useState(true);

  const getThemeIcon = () => {
    switch (themeMode) {
      case 'dark':
        return Moon;
      case 'light':
        return Sun;
      case 'system':
        return Monitor;
      default:
        return Sun;
    }
  };

  const getThemeLabel = () => {
    switch (themeMode) {
      case 'dark':
        return 'Dark mode';
      case 'light':
        return 'Light mode';
      case 'system':
        return 'Follow system';
      default:
        return 'Light mode';
    }
  };

  const toggleTheme = () => {
    const modes: ThemeMode[] = ['light', 'dark', 'system'];
    const currentIndex = modes.indexOf(themeMode);
    const nextIndex = (currentIndex + 1) % modes.length;
    setThemeMode(modes[nextIndex]);
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Header */}
      <View
        style={[
          styles.header,
          { backgroundColor: theme.cardBackground, borderBottomColor: theme.border },
        ]}
      >
        <Text style={[styles.headerTitle, { color: theme.text }]}>Settings</Text>
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Notifications Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>NOTIFICATIONS</Text>
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <SettingItem
              icon={Bell}
              title="Push Notifications"
              subtitle="Receive important alerts and updates"
              theme={theme}
              rightElement={
                <Switch
                  value={notificationsEnabled}
                  onValueChange={setNotificationsEnabled}
                  trackColor={{ false: '#94a3b8', true: '#3b82f6' }}
                  thumbColor={notificationsEnabled ? '#ffffff' : '#f4f4f5'}
                />
              }
            />
          </View>
        </View>

        {/* Appearance Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>APPEARANCE</Text>
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <SettingItem
              icon={getThemeIcon()}
              title="Theme"
              subtitle={getThemeLabel()}
              theme={theme}
              onPress={toggleTheme}
              showChevron={true}
            />
          </View>
        </View>

        {/* Driving Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>DRIVING</Text>
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <SettingItem
              icon={Activity}
              title="Accelerometer Settings"
              subtitle="Configure driving behavior detection"
              theme={theme}
              onPress={() => navigation.navigate('AccelerometerSettings')}
              showChevron={true}
            />
          </View>
        </View>

        {/* Development & Testing Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
            DEVELOPMENT & TESTING
          </Text>
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <SettingItem
              icon={TestTube}
              title="Algorithm Demo & Validation"
              subtitle="Comprehensive testing and demo suite"
              theme={theme}
              onPress={() => navigation.navigate('ComprehensiveDemo')}
              showChevron={true}
            />
          </View>
        </View>

        {/* Removed Support Section and Sign Out button */}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    marginTop: 24,
  },
  lastSection: {
    marginBottom: 32,
  },
  sectionTitle: {
    paddingHorizontal: 16,
    paddingBottom: 8,
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  card: {
    marginHorizontal: 16,
    borderRadius: 12,
    overflow: 'hidden',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
  },
  iconContainer: {
    marginRight: 12,
  },
  contentContainer: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  settingSubtitle: {
    fontSize: 14,
    marginTop: 2,
  },
  rightContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
});
