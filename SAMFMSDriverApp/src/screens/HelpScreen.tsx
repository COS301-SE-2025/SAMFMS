import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Linking } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Phone, FileText, ChevronRight, Github } from 'lucide-react-native';
import { useTheme } from '../contexts/ThemeContext';

interface HelpItemProps {
  icon: any;
  title: string;
  subtitle: string;
  onPress: () => void;
  theme: {
    cardBackground: string;
    text: string;
    textSecondary: string;
    border: string;
  };
}

const HelpItem: React.FC<HelpItemProps> = ({ icon: Icon, title, subtitle, onPress, theme }) => (
  <TouchableOpacity
    style={[
      styles.helpItem,
      { backgroundColor: theme.cardBackground, borderBottomColor: theme.border },
    ]}
    onPress={onPress}
  >
    <View style={styles.helpItemLeft}>
      <View style={styles.iconContainer}>
        <Icon size={24} color={theme.text} />
      </View>
      <View style={styles.helpItemContent}>
        <Text style={[styles.helpItemTitle, { color: theme.text }]}>{title}</Text>
        <Text style={[styles.helpItemSubtitle, { color: theme.textSecondary }]}>{subtitle}</Text>
      </View>
    </View>
    <ChevronRight size={20} color={theme.textSecondary} />
  </TouchableOpacity>
);

interface FAQItemProps {
  question: string;
  answer: string;
  theme: {
    cardBackground: string;
    text: string;
    textSecondary: string;
    border: string;
  };
}

const FAQItem: React.FC<FAQItemProps> = ({ question, answer, theme }) => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <TouchableOpacity
      style={[
        styles.faqItem,
        { backgroundColor: theme.cardBackground, borderBottomColor: theme.border },
      ]}
      onPress={() => setIsExpanded(!isExpanded)}
    >
      <View style={styles.faqHeader}>
        <Text style={[styles.faqQuestion, { color: theme.text }]}>{question}</Text>
        <ChevronRight
          size={20}
          color={theme.textSecondary}
          style={[styles.faqChevron, isExpanded && styles.faqChevronRotated]}
        />
      </View>
      {isExpanded && (
        <Text style={[styles.faqAnswer, { color: theme.textSecondary }]}>{answer}</Text>
      )}
    </TouchableOpacity>
  );
};

export default function HelpScreen() {
  const { theme } = useTheme();

  const openPhone = () => {
    Linking.openURL('tel:+27842611935'); // Updated to the correct phone number
  };

  const openUserGuide = () => {
    Linking.openURL(
      'https://github.com/COS301-SE-2025/SAMFMS/blob/main/docs/Demo3/SAMFMS%20User%20Manual.pdf'
    );
  };

  const openGitHub = () => {
    Linking.openURL('https://github.com/COS301-SE-2025/SAMFMS');
  };

  const faqData = [
    {
      question: 'How do I start a trip in the driver app?',
      answer:
        'To start a trip, navigate to the Dashboard and look for active trip assignments. Tap on a scheduled trip and follow the on-screen instructions to begin your route.',
    },
    {
      question: 'How does the speed monitoring feature work?',
      answer:
        "The app continuously monitors your speed using GPS and compares it to posted speed limits. You'll receive alerts if you exceed the limit, and violations are automatically reported to fleet managers.",
    },
    {
      question: 'What should I do if I detect harsh braking or acceleration?',
      answer:
        'The app automatically detects harsh driving behaviors using accelerometer data. These events are logged for safety analysis. Focus on smooth, gradual acceleration and braking to maintain safe driving scores.',
    },
    {
      question: 'How can I view my driving performance?',
      answer:
        'Your driving performance, including speed violations and harsh driving events, can be viewed in the Account section under your profile. This helps you track and improve your driving habits.',
    },
    {
      question: "What happens if there's an emergency during my trip?",
      answer:
        'Use the emergency features in the app or contact emergency services directly. The app includes location tracking that can help dispatchers locate you quickly in case of emergencies.',
    },
    {
      question: 'Can I pause a trip if needed?',
      answer:
        'Yes, you can pause an active trip using the pause button on the active trip screen. Make sure to resume the trip when you continue driving to maintain accurate tracking.',
    },
  ];

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Header */}
      <View
        style={[
          styles.header,
          { backgroundColor: theme.cardBackground, borderBottomColor: theme.border },
        ]}
      >
        <Text style={[styles.headerTitle, { color: theme.text }]}>Help & Support</Text>
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Contact Support */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Contact Support</Text>
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <HelpItem
              icon={Phone}
              title="Phone Support"
              subtitle="+27 84 261 1935"
              onPress={openPhone}
              theme={theme}
            />
          </View>
        </View>

        {/* Resources */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Resources</Text>
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <HelpItem
              icon={FileText}
              title="User Manual"
              subtitle="Complete guide for using the app"
              onPress={openUserGuide}
              theme={theme}
            />
            <HelpItem
              icon={Github}
              title="GitHub Repository"
              subtitle="View source code and project info"
              onPress={openGitHub}
              theme={theme}
            />
          </View>
        </View>

        {/* Frequently Asked Questions */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Frequently Asked Questions
          </Text>
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            {faqData.map((faq, index) => (
              <FAQItem key={index} question={faq.question} answer={faq.answer} theme={theme} />
            ))}
          </View>
        </View>

        {/* Emergency Contact section removed */}
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
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    paddingHorizontal: 16,
  },
  card: {
    marginHorizontal: 16,
    borderRadius: 12,
    overflow: 'hidden',
  },
  helpItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
  },
  helpItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  iconContainer: {
    marginRight: 12,
  },
  helpItemContent: {
    flex: 1,
  },
  helpItemTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  helpItemSubtitle: {
    fontSize: 14,
    marginTop: 2,
  },
  faqItem: {
    padding: 16,
    borderBottomWidth: 1,
  },
  faqHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  faqQuestion: {
    fontSize: 16,
    fontWeight: '500',
    flex: 1,
  },
  faqChevron: {
    marginLeft: 8,
  },
  faqChevronRotated: {
    transform: [{ rotate: '90deg' }],
  },
  faqAnswer: {
    fontSize: 14,
    marginTop: 12,
    lineHeight: 20,
  },
  // Emergency styles removed
});
