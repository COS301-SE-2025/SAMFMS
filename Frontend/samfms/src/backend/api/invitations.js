/**
 * User Invitation Management API
 * All invitation-related API endpoints and functions
 */
import { httpClient } from '../services/httpClient';
import { buildApiUrl } from '../../config/apiConfig';

/**
 * Send an invitation to a user
 * @param {Object} invitationData - Invitation data (email, role, etc.)
 * @returns {Promise<Object>} Invitation response
 */
export const sendInvitation = async invitationData => {
  try {
    return await httpClient.post('/auth/invite-user', invitationData);
  } catch (error) {
    console.error('Error sending invitation:', error);
    throw error;
  }
};

/**
 * Get list of pending invitations
 * @returns {Promise<Array>} List of pending invitations
 */
export const getPendingInvitations = async () => {
  try {
    return await httpClient.get('/auth/invitations');
  } catch (error) {
    console.error('Error fetching pending invitations:', error);
    throw error;
  }
};

/**
 * Resend an invitation
 * @param {string} email - Email address to resend invitation to
 * @returns {Promise<Object>} Resend response
 */
export const resendInvitation = async email => {
  try {
    return await httpClient.post('/auth/resend-invitation', { email });
  } catch (error) {
    console.error(`Error resending invitation to ${email}:`, error);
    throw error;
  }
};

/**
 * Cancel an invitation
 * @param {string} email - Email address to cancel invitation for
 * @returns {Promise<Object>} Cancellation response
 */
export const cancelInvitation = async email => {
  try {
    const endpoint = `/admin/cancel-invitation?email=${encodeURIComponent(email)}`;
    return await httpClient.delete(endpoint);
  } catch (error) {
    console.error(`Error canceling invitation for ${email}:`, error);
    throw error;
  }
};

/**
 * Verify invitation OTP (public endpoint - no auth required)
 * @param {string} email - Email address
 * @param {string} otp - OTP code
 * @returns {Promise<Object>} Verification response
 */
export const verifyInvitationOTP = async (email, otp) => {
  try {
    // Use direct fetch for public endpoints to avoid automatic token handling
    const response = await fetch(buildApiUrl('/auth/verify-otp'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, otp }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to verify OTP');
    }

    return await response.json();
  } catch (error) {
    console.error('Error verifying OTP:', error);
    throw error;
  }
};

/**
 * Complete user registration (public endpoint - no auth required)
 * @param {string} email - Email address
 * @param {string} otp - OTP code
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {Promise<Object>} Registration response
 */
export const completeUserRegistration = async (email, otp, username, password) => {
  try {
    // Use direct fetch for public endpoints to avoid automatic token handling
    const response = await fetch(buildApiUrl('/auth/complete-registration'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, otp, username, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to complete registration');
    }

    return await response.json();
  } catch (error) {
    console.error('Error completing registration:', error);
    throw error;
  }
};
