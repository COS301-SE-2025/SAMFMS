import React from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  useColorScheme,
  StyleSheet,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Phone, Mail, FileText, ChevronRight } from 'lucide-react-native';

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
  const isDarkMode = useColorScheme() === 'dark';

  const theme = {
    background: isDarkMode ? '#0f172a' : '#f8fafc',
    cardBackground: isDarkMode ? '#1e293b' : '#ffffff',
    text: isDarkMode ? '#f1f5f9' : '#1e293b',
    textSecondary: isDarkMode ? '#94a3b8' : '#64748b',
    accent: '#3b82f6',
    border: isDarkMode ? '#334155' : '#e2e8f0',
  };

  const openEmail = () => {
    Linking.openURL('mailto:support@samfms.com');
  };

  const openPhone = () => {
    Linking.openURL('tel:+15551234567');
  };

  const openUserGuide = () => {
    console.log('Open User Guide');
  };

  const faqData = [
    {
      question: 'How do I start a new trip?',
      answer:
        "To start a new trip, go to the Dashboard and tap on 'Start Trip'. Follow the prompts to enter your destination and route details.",
    },
    {
      question: 'How do I report vehicle issues?',
      answer:
        "You can report vehicle issues by going to the 'Check Vehicle' section in the dashboard and selecting 'Report Issue'. Describe the problem and submit the report.",
    },
    {
      question: 'How do I check my trip history?',
      answer:
        "Your trip history is available in the Account section. Tap on 'Trip History' to view all your past trips with details and routes.",
    },
    {
      question: 'What should I do if I encounter an emergency?',
      answer:
        'In case of an emergency, use the emergency button in the app or call emergency services directly. The app will automatically alert the dispatch center.',
    },
    {
      question: 'How do I update my profile information?',
      answer:
        'Profile information can be updated by contacting your fleet manager or through the web portal. Some basic information can be viewed in the Account section.',
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
              icon={Mail}
              title="Email Support"
              subtitle="support@samfms.com"
              onPress={openEmail}
              theme={theme}
            />
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
              title="User Guide"
              subtitle="Complete guide for using the app"
              onPress={openUserGuide}
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

        {/* Emergency Contact */}
        <View style={[styles.section, styles.lastSection]}>
          <View
            style={[styles.emergencyCard, { backgroundColor: '#fef2f2', borderColor: '#fecaca' }]}
          >
            <View style={styles.emergencyContent}>
              <Text style={[styles.emergencyTitle, { color: '#dc2626' }]}>Emergency Contact</Text>
              <Text style={[styles.emergencySubtitle, { color: '#7f1d1d' }]}>
                For immediate assistance or emergencies, call:
              </Text>
              <TouchableOpacity
                style={styles.emergencyButton}
                onPress={() => Linking.openURL('tel:911')}
              >
                <Phone size={20} color="#ffffff" />
                <Text style={styles.emergencyButtonText}>Emergency: 911</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
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
  emergencyCard: {
    marginHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
  },
  emergencyContent: {
    alignItems: 'center',
  },
  emergencyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  emergencySubtitle: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 16,
  },
  emergencyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#dc2626',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  emergencyButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
});
