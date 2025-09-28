import React, {useState} from 'react';
import {Button} from '../ui/button';
import {resetPasswordWithOTP} from '../../backend/API';

const ForgotPasswordModal = ({isOpen, onClose, email, onSuccess}) => {
    const [formData, setFormData] = useState({
        otp: '',
        newPassword: '',
        confirmPassword: '',
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [passwordError, setPasswordError] = useState('');

    const handleChange = (e) => {
        const {name, value} = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value,
        }));

        // Clear password error when user starts typing
        if (name === 'newPassword' || name === 'confirmPassword') {
            setPasswordError('');
        }

        // Clear general error
        setError('');
    };

    const validateForm = () => {
        // Validate password match
        if (formData.newPassword !== formData.confirmPassword) {
            setPasswordError('Passwords do not match');
            return false;
        }

        // Validate password length
        if (formData.newPassword.length < 6) {
            setPasswordError('Password must be at least 6 characters long');
            return false;
        }

        // Validate OTP
        if (!formData.otp || formData.otp.trim().length === 0) {
            setError('Please enter the OTP sent to your email');
            return false;
        }

        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        setError('');
        setLoading(true);

        try {
            await resetPasswordWithOTP(email, formData.otp.trim(), formData.newPassword);

            // Reset form
            setFormData({
                otp: '',
                newPassword: '',
                confirmPassword: '',
            });

            // Call success callback
            if (onSuccess) {
                onSuccess('Password reset successfully! You can now log in with your new password.');
            }

            // Close modal
            onClose();
        } catch (err) {
            setError(err.message || 'Failed to reset password. Please check your OTP and try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        setFormData({
            otp: '',
            newPassword: '',
            confirmPassword: '',
        });
        setError('');
        setPasswordError('');
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
            style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                position: 'fixed'
            }}
        >
            <div
                className="bg-card bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 rounded-lg shadow-xl p-6 w-full max-w-md border border-border relative"
                style={{
                    maxHeight: '90vh',
                    overflowY: 'auto',
                    margin: 'auto'
                }}
            >
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-semibold text-foreground">
                        Reset Password
                    </h2>
                    <button
                        onClick={handleClose}
                        className="text-muted-foreground hover:text-foreground text-2xl"
                    >
                        ×
                    </button>
                </div>

                <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-md">
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                        An OTP has been sent to <strong>{email}</strong>. Please check your email and enter the code below along with your new password.
                    </p>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-md">
                        <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1 text-foreground">
                            Email
                        </label>
                        <input
                            type="email"
                            value={email}
                            disabled
                            className="w-full p-2 border border-border rounded-md bg-muted text-muted-foreground cursor-not-allowed"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1 text-foreground">
                            OTP Code *
                        </label>
                        <input
                            type="text"
                            name="otp"
                            value={formData.otp}
                            onChange={handleChange}
                            className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary"
                            placeholder="Enter the 6-digit code from your email"
                            maxLength="10"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1 text-foreground">
                            New Password *
                        </label>
                        <input
                            type="password"
                            name="newPassword"
                            value={formData.newPassword}
                            onChange={handleChange}
                            className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary"
                            placeholder="Enter your new password"
                            required
                            minLength="6"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1 text-foreground">
                            Re-enter New Password *
                        </label>
                        <input
                            type="password"
                            name="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            className="w-full p-2 border border-border rounded-md bg-background text-foreground focus:ring-primary focus:border-primary"
                            placeholder="Confirm your new password"
                            required
                            minLength="6"
                        />
                    </div>

                    {passwordError && (
                        <div className="text-sm text-destructive bg-destructive/10 p-2 rounded border border-destructive/20">
                            {passwordError}
                        </div>
                    )}

                    <div className="flex justify-end space-x-3 pt-4">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleClose}
                            disabled={loading}
                        >
                            Cancel
                        </Button>
                        <Button type="submit" disabled={loading}>
                            {loading ? 'Resetting Password...' : 'Reset Password'}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ForgotPasswordModal;