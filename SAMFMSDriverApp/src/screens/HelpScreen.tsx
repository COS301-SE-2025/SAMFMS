import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Linking } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Phone, Mail, FileText, ChevronRight } from 'lucide-react-native';
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

  const openEmail = () => {
    Linking.openURL('mailto:support@samfms.com');
  };

  const openPhone = () => {
    Linking.openURL('tel:+27118876543'); // Updated to the correct phone number
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
