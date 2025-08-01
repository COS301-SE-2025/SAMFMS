import React, {useState} from 'react';
import {Button} from './ui/button';

const mockLayouts = [
    {id: 'default', name: 'Default Layout'},
    {id: 'compact', name: 'Compact Layout'},
    {id: 'wide', name: 'Wide Layout'},
];

const DashboardLayoutToolbar = () => {
    const [selectedLayout, setSelectedLayout] = useState(mockLayouts[0].id);
    const [showCreatePopup, setShowCreatePopup] = useState(false);
    const [newLayoutName, setNewLayoutName] = useState('');

    const handleLayoutChange = (e) => {
        setSelectedLayout(e.target.value);
    };

    const handleCreateLayout = (e) => {
        e.preventDefault();
        // Here you would add the new layout logic
        setShowCreatePopup(false);
        setNewLayoutName('');
    };

    return (
        <div className="flex items-center gap-4 mb-8">
            <div>
                <label className="font-medium mr-2">Choose Layout:</label>
                <select
                    value={selectedLayout}
                    onChange={handleLayoutChange}
                    className="border rounded px-2 py-1"
                >
                    {mockLayouts.map((layout) => (
                        <option key={layout.id} value={layout.id}>
                            {layout.name}
                        </option>
                    ))}
                </select>
            </div>
            <Button onClick={() => setShowCreatePopup(true)} variant="outline">
                Create Layout
            </Button>
            <Button variant="outline" disabled>
                Edit Layout
            </Button>

            {/* Create Layout Popup */}
            {showCreatePopup && (
                <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-30 z-50">
                    <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-sm shadow-lg">
                        <h3 className="text-lg font-semibold mb-4">Create New Layout</h3>
                        <form onSubmit={handleCreateLayout} className="space-y-4">
                            <div>
                                <label className="block font-medium mb-1">Layout Name</label>
                                <input
                                    type="text"
                                    value={newLayoutName}
                                    onChange={(e) => setNewLayoutName(e.target.value)}
                                    required
                                    className="w-full border rounded p-2"
                                    placeholder="Enter layout name"
                                />
                            </div>
                            <div className="flex justify-end space-x-2">
                                <Button
                                    type="button"
                                    variant="ghost"
                                    onClick={() => setShowCreatePopup(false)}
                                >
                                    Cancel
                                </Button>
                                <Button type="submit">Create</Button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DashboardLayoutToolbar;