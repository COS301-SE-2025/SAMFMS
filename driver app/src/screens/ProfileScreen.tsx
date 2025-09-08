import React from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
} from 'react-native';
import {
  Card,
  Text,
  Button,
  List,
  Avatar,
} from 'react-native-paper';
import {useAuth} from '../context/AuthContext';
import {theme} from '../theme/theme';

const ProfileScreen = ({navigation}: any) => {
  const {user, logout} = useAuth();

  const handleLogout = async () => {
    await logout();
    navigation.replace('Login');
  };

  const handleEditProfile = () => {
    // Navigate to edit profile screen (to be implemented)
    console.log('Edit profile');
  };

  const handleChangePassword = () => {
    // Navigate to change password screen (to be implemented)
    console.log('Change password');
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Profile Header */}
        <Card style={styles.profileCard}>
          <Card.Content style={styles.profileContent}>
            <Avatar.Text
              size={80}
              label={user?.username?.substring(0, 2).toUpperCase() || 'DR'}
              style={styles.avatar}
            />
            <Text style={styles.userName}>{user?.username}</Text>
            <Text style={styles.userEmail}>{user?.email}</Text>
            <Text style={styles.userRole}>{user?.role}</Text>
          </Card.Content>
        </Card>

        {/* Account Settings */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Account Settings</Text>
            <List.Item
              title="Edit Profile"
              description="Update your personal information"
              left={(props) => <List.Icon {...props} icon="account-edit" />}
              right={(props) => <List.Icon {...props} icon="chevron-right" />}
              onPress={handleEditProfile}
            />
            <List.Item
              title="Change Password"
              description="Update your password"
              left={(props) => <List.Icon {...props} icon="lock" />}
              right={(props) => <List.Icon {...props} icon="chevron-right" />}
              onPress={handleChangePassword}
            />
            <List.Item
              title="Notifications"
              description="Manage notification preferences"
              left={(props) => <List.Icon {...props} icon="bell" />}
              right={(props) => <List.Icon {...props} icon="chevron-right" />}
              onPress={() => console.log('Notifications')}
            />
          </Card.Content>
        </Card>

        {/* App Settings */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>App Settings</Text>
            <List.Item
              title="Language"
              description="English"
              left={(props) => <List.Icon {...props} icon="translate" />}
              right={(props) => <List.Icon {...props} icon="chevron-right" />}
              onPress={() => console.log('Language')}
            />
            <List.Item
              title="Theme"
              description="System default"
              left={(props) => <List.Icon {...props} icon="palette" />}
              right={(props) => <List.Icon {...props} icon="chevron-right" />}
              onPress={() => console.log('Theme')}
            />
          </Card.Content>
        </Card>

        {/* Support */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Support</Text>
            <List.Item
              title="Help Center"
              description="Get help and support"
              left={(props) => <List.Icon {...props} icon="help-circle" />}
              right={(props) => <List.Icon {...props} icon="chevron-right" />}
              onPress={() => console.log('Help')}
            />
            <List.Item
              title="Contact Support"
              description="Reach out to our support team"
              left={(props) => <List.Icon {...props} icon="email" />}
              right={(props) => <List.Icon {...props} icon="chevron-right" />}
              onPress={() => console.log('Contact Support')}
            />
            <List.Item
              title="About"
              description="App version and information"
              left={(props) => <List.Icon {...props} icon="information" />}
              right={(props) => <List.Icon {...props} icon="chevron-right" />}
              onPress={() => console.log('About')}
            />
          </Card.Content>
        </Card>

        {/* Logout Button */}
        <Card style={styles.card}>
          <Card.Content>
            <Button
              mode="contained"
              icon="logout"
              onPress={handleLogout}
              buttonColor={theme.colors.error}
              textColor="#fff"
              style={styles.logoutButton}>
              Logout
            </Button>
          </Card.Content>
        </Card>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  profileCard: {
    marginBottom: 16,
    backgroundColor: theme.colors.primary,
  },
  profileContent: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  avatar: {
    marginBottom: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.8,
    marginBottom: 4,
  },
  userRole: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.7,
    textTransform: 'capitalize',
  },
  card: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
    color: theme.colors.primary,
  },
  logoutButton: {
    marginTop: 8,
  },
});

export default ProfileScreen;
