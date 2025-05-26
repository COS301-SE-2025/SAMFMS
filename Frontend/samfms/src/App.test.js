import { render, screen } from '@testing-library/react';
import App from './App';

test('renders without crashing', () => {
  // This test just verifies the app renders without throwing an error
  render(<App />);
});
