# SAMFMS Driver App

A React Native mobile application for drivers in the SAMFMS fleet management system.

## Features

- **Authentication**: Secure login for drivers
- **Dashboard**: Overview of trips, notifications, and quick actions
- **Trip Management**: View and manage assigned trips
- **Vehicle Inspection**: Pre-trip vehicle inspection checklist
- **Maintenance Reporting**: Report vehicle issues and maintenance needs
- **Profile Management**: Driver profile and settings

## Prerequisites

Before running the app, ensure you have:

1. **Node.js** (v16 or later): [Download Node.js](https://nodejs.org/)
2. **React Native CLI**: Install globally with `npm install -g react-native-cli`
3. **Android Studio** (for Android development): [Download Android Studio](https://developer.android.com/studio)
4. **Xcode** (for iOS development, Mac only): Available from the Mac App Store

### Android Setup
- Install Android Studio with Android SDK
- Set up an Android Virtual Device (AVD) or connect a physical device
- Ensure USB debugging is enabled on physical devices

### iOS Setup (Mac only)
- Install Xcode from the App Store
- Install iOS Simulator
- For physical devices, you'll need an Apple Developer account

## Installation

1. **Navigate to the driver app directory**:
   ```bash
   cd "c:\Users\user\OneDrive\Documents\capstone\repo\SAMFMS\driver app"
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **For iOS (Mac only), install CocoaPods dependencies**:
   ```bash
   cd ios && pod install && cd ..
   ```

## Running the App

### Start the Metro bundler:
```bash
npm start
```

### Run on Android:
```bash
npm run android
```

### Run on iOS (Mac only):
```bash
npm run ios
```

## Development Commands

- **Start Metro bundler**: `npm start`
- **Run Android**: `npm run android`
- **Run iOS**: `npm run ios`
- **Run tests**: `npm test`
- **Lint code**: `npm run lint`
- **Build Android APK**: `npm run build:android`
- **Build iOS**: `npm run build:ios`

## Project Structure

```
src/
├── App.tsx                 # Main app component
├── context/
│   └── AuthContext.tsx     # Authentication context
├── navigation/
│   └── MainTabNavigator.tsx # Bottom tab navigation
├── screens/
│   ├── LoginScreen.tsx
│   ├── DashboardScreen.tsx
│   ├── TripScreen.tsx
│   ├── VehicleScreen.tsx
│   ├── ProfileScreen.tsx
│   ├── VehicleInspectionScreen.tsx
│   ├── TripDetailsScreen.tsx
│   └── MaintenanceReportScreen.tsx
├── services/
│   └── apiService.ts       # API service layer
└── theme/
    └── theme.ts            # App theme configuration
```

## Configuration

1. **API Configuration**: Update the `API_BASE_URL` in `src/services/apiService.ts` to point to your SAMFMS backend server.

2. **Theme Customization**: Modify colors and styles in `src/theme/theme.ts`.

## Troubleshooting

### Common Issues:

1. **Metro bundler port conflict**: 
   - Kill existing Metro processes: `npx react-native start --reset-cache`

2. **Android build issues**:
   - Clean project: `cd android && ./gradlew clean && cd ..`
   - Rebuild: `npm run android`

3. **iOS build issues (Mac only)**:
   - Clean Xcode build folder: Product → Clean Build Folder
   - Reinstall pods: `cd ios && pod install && cd ..`

4. **Dependencies not found**:
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall: `rm -rf node_modules && npm install`

## Development Notes

- The app uses TypeScript for type safety
- React Native Paper for UI components
- React Navigation for screen navigation
- AsyncStorage for local data persistence
- Axios for HTTP requests

## API Integration

The app is configured to work with the SAMFMS backend API. Ensure your backend server is running and accessible before testing the app functionality.

## Building for Production

### Android:
```bash
cd android
./gradlew assembleRelease
```

### iOS (Mac only):
1. Open `ios/SAMFMSDriverApp.xcworkspace` in Xcode
2. Select your device/simulator
3. Product → Archive
4. Follow the signing and distribution process

## Support

For development support or issues, refer to the main SAMFMS project documentation.
