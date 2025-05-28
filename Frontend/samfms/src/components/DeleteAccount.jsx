import React, {useState} from 'react';
import {Button} from './ui/button';

const DeleteAccount = () => {
    const [showPopup, setShowPopup] = useState(false);
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');

    const handleDeleteClick = () => {
        setShowPopup(true);
        setPassword('');
        setConfirmPassword('');
        setError('');
    };

    const handleClose = () => {
        setShowPopup(false);
        setPassword('');
        setConfirmPassword('');
        setError('');
    };

    const handleConfirmDelete = (e) => {
        e.preventDefault();
        if (password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }
        // Add delete logic here
        setShowPopup(false);
        // Optionally show a success message or redirect
    };

    return (
        <div className="bg-card p-6 rounded-lg shadow-md border border-border mt-8">
            <h2 className="text-xl font-semibold mb-2 text-red-600">Delete Account</h2>
            <p className="mb-4 text-red-500">
                Warning: Deleting your account is <strong>permanent</strong> and cannot be undone. All your data will be lost.
            </p>
            <Button variant="destructive" onClick={handleDeleteClick}>
                Delete Account
            </Button>

            {showPopup && (
                <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-30 z-50">
                    <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-sm shadow-lg">
                        <h3 className="text-lg font-semibold mb-4 text-red-600">Confirm Account Deletion</h3>
                        <form onSubmit={handleConfirmDelete} className="space-y-4">
                            <div>
                                <label className="block font-medium mb-1">Password</label>
                                <input
                                    type="password"
                                    className="w-full border rounded p-2"
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    required
                                />
                            </div>
                            <div>
                                <label className="block font-medium mb-1">Confirm Password</label>
                                <input
                                    type="password"
                                    className="w-full border rounded p-2"
                                    value={confirmPassword}
                                    onChange={e => setConfirmPassword(e.target.value)}
                                    required
                                />
                            </div>
                            {error && <div className="text-red-500 text-sm">{error}</div>}
                            <div className="flex justify-end space-x-2">
                                <Button type="button" variant="ghost" onClick={handleClose}>
                                    Cancel
                                </Button>
                                <Button type="submit" variant="destructive">
                                    Delete Account
                                </Button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DeleteAccount;