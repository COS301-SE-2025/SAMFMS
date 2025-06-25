// Helper functions for cookie management
export const setCookie = (name, value, days, options = {}) => {
  let expires = '';
  if (days) {
    const date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    expires = '; expires=' + date.toUTCString();
  }

  // Security flags - adjust for HTTP development
  let securityFlags = '; path=/';
  
  // Only use Secure flag for HTTPS
  if (window.location.protocol === 'https:') {
    securityFlags += '; Secure';
  }
  
  // Use Lax instead of Strict for better compatibility
  securityFlags += '; SameSite=Lax';

  // Note: HttpOnly cannot be set from JavaScript for security reasons
  // It should be set by the server when setting sensitive cookies
  if (options.httpOnly) {
    console.warn('HttpOnly flag cannot be set from JavaScript. This should be set by the server.');
  }

  document.cookie = name + '=' + (value || '') + expires + securityFlags;
};

export const getCookie = name => {
  const nameEQ = name + '=';
  const ca = document.cookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
  }
  return null;
};

export const eraseCookie = name => {
  document.cookie =
    name + '=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT; Secure; SameSite=Strict;';
};

// Additional helper functions for consistency
export const getToken = () => {
  return getCookie('token');
};

export const deleteCookie = name => {
  eraseCookie(name);
};
