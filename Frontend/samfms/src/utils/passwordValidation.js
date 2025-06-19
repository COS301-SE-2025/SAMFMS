// Password validation utilities
export const validatePassword = password => {
  const errors = [];

  if (!password) {
    return ['Password is required'];
  }

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }

  if (!/(?=.*[a-z])/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }

  if (!/(?=.*[A-Z])/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }

  if (!/(?=.*\d)/.test(password)) {
    errors.push('Password must contain at least one number');
  }

  if (!/(?=.*[@$!%*?&])/.test(password)) {
    errors.push('Password must contain at least one special character (@$!%*?&)');
  }

  return errors;
};

export const getPasswordStrength = password => {
  if (!password) return { score: 0, text: 'Very Weak', color: 'text-red-500' };

  let score = 0;

  // Length
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;

  // Character types
  if (/[a-z]/.test(password)) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[@$!%*?&]/.test(password)) score += 1;

  // Bonus for variety
  if (password.length >= 16) score += 1;

  if (score <= 2) {
    return { score, text: 'Weak', color: 'text-red-500' };
  } else if (score <= 4) {
    return { score, text: 'Fair', color: 'text-yellow-500' };
  } else if (score <= 5) {
    return { score, text: 'Good', color: 'text-blue-500' };
  } else {
    return { score, text: 'Strong', color: 'text-green-500' };
  }
};

export const PasswordStrengthIndicator = ({ password }) => {
  const strength = getPasswordStrength(password);
  const width = Math.max((strength.score / 6) * 100, 10);

  return (
    <div className="mt-2">
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs text-muted-foreground">Password Strength:</span>
        <span className={`text-xs font-medium ${strength.color}`}>{strength.text}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full transition-all duration-300 ${
            strength.score <= 2
              ? 'bg-red-500'
              : strength.score <= 4
              ? 'bg-yellow-500'
              : strength.score <= 5
              ? 'bg-blue-500'
              : 'bg-green-500'
          }`}
          style={{ width: `${width}%` }}
        ></div>
      </div>
    </div>
  );
};

export const PasswordRequirements = ({ password }) => {
  const requirements = [
    { test: p => p.length >= 8, text: 'At least 8 characters' },
    { test: p => /[a-z]/.test(p), text: 'One lowercase letter' },
    { test: p => /[A-Z]/.test(p), text: 'One uppercase letter' },
    { test: p => /\d/.test(p), text: 'One number' },
    { test: p => /[@$!%*?&]/.test(p), text: 'One special character (@$!%*?&)' },
  ];

  return (
    <div className="mt-2 space-y-1">
      {requirements.map((req, index) => {
        const isValid = req.test(password || '');
        return (
          <div key={index} className="flex items-center text-xs">
            <div
              className={`w-3 h-3 rounded-full mr-2 flex items-center justify-center ${
                isValid ? 'bg-green-500 text-white' : 'bg-gray-300'
              }`}
            >
              {isValid && '✓'}
            </div>
            <span className={isValid ? 'text-green-600' : 'text-muted-foreground'}>{req.text}</span>
          </div>
        );
      })}
    </div>
  );
};
