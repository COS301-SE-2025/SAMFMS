import React, { useState, useEffect } from 'react';
import { Search, Calendar, Clock, Download, Filter } from 'lucide-react';

const LocationHistory = ({ vehicles, drivers }) => {
  const [activeTab, setActiveTab] = useState('vehicles');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItems, setSelectedItems] = useState([]);
  const [timeRange, setTimeRange] = useState('24h');
  const [customDate, setCustomDate] = useState(new Date().toISOString().split('T')[0]);
  const [filterType, setFilterType] = useState('all');

  // Sample history data
  const [historyData, setHistoryData] = useState([
    {
      timestamp: '08:15 AM',
      type: 'start',
      description: 'Started trip',
      location: 'Depot Location (37.7749, -122.4194)',
      vehicleId: 'VEH-001',
    },
    {
      timestamp: '09:22 AM',
      type: 'speed',
      description: 'Speeding Event',
      location: '95 km/h in 70 km/h zone',
      vehicleId: 'VEH-001',
    },
    {
      timestamp: '09:45 AM',
      type: 'arrival',
      description: 'Arrival at client',
      location: 'Client HQ (37.7694, -122.4862)',
      vehicleId: 'VEH-001',
    },
    {
      timestamp: '10:30 AM',
      type: 'departure',
      description: 'Departed from client',
      location: 'Client HQ (37.7694, -122.4862)',
      vehicleId: 'VEH-001',
    },
    {
      timestamp: '10:55 AM',
      type: 'location',
      description: 'Current Location',
      location: 'On route (37.7833, -122.4167)',
      vehicleId: 'VEH-001',
    },
    {
      timestamp: '08:30 AM',
      type: 'start',
      description: 'Started trip',
      location: 'Service Center (37.7775, -122.4254)',
      vehicleId: 'VEH-002',
    },
    {
      timestamp: '09:15 AM',
      type: 'idle',
      description: 'Idle time',
      location: 'Downtown (37.7833, -122.4167)',
      vehicleId: 'VEH-002',
    },
    {
      timestamp: '10:45 AM',
      type: 'geofence',
      description: 'Entered restricted zone',
      location: 'No-Go Zone (37.7833, -122.4167)',
      vehicleId: 'VEH-002',
    },
  ]);

  // Filter the list items based on the active tab and search term
  const filteredItems =
    activeTab === 'vehicles'
      ? vehicles.filter(
          v =>
            v.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
            v.make.toLowerCase().includes(searchTerm.toLowerCase()) ||
            v.model.toLowerCase().includes(searchTerm.toLowerCase())
        )
      : drivers.filter(
          d =>
            d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            d.id.toLowerCase().includes(searchTerm.toLowerCase())
        );

  // Filter history data based on selected items and filter type
  const filteredHistoryData = historyData.filter(item => {
    // Only show data for selected vehicles
    const matchesVehicle = selectedItems.some(selected => selected.id === item.vehicleId);

    // Filter by event type if specified
    const matchesType = filterType === 'all' || item.type === filterType;

    return matchesVehicle && matchesType;
  });

  // Add or remove item from selection
  const toggleSelection = item => {
    if (selectedItems.some(selected => selected.id === item.id)) {
      setSelectedItems(selectedItems.filter(selected => selected.id !== item.id));
    } else {
      setSelectedItems([...selectedItems, item]);
    }
  };

  // Export history data as CSV
  const exportData = () => {
    if (filteredHistoryData.length === 0) return;

    // Format data for CSV
    const csvContent = [
      'Time,Event,Description,Location',
      ...filteredHistoryData.map(
        item => `${item.timestamp},"${item.description}","${item.location}"`
      ),
    ].join('\\n');

    // Create download link
    const encodedUri = encodeURI(`data:text/csv;charset=utf-8,${csvContent}`);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `vehicle_history_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);

    // Trigger download and clean up
    link.click();
    document.body.removeChild(link);
  };

  // Get the title for the history section based on selected items
  const getHistoryTitle = () => {
    if (selectedItems.length === 0) {
      return 'No vehicle selected';
    } else if (selectedItems.length === 1) {
      const item = selectedItems[0];
      if (activeTab === 'vehicles') {
        return `${item.make} ${item.model} (${item.id}) - History`;
      } else {
        return `${item.name} (${item.id}) - History`;
      }
    } else {
      return `Multiple ${activeTab} selected`;
    }
  };

  return (
    <div className="bg-card rounded-lg shadow-md p-6 border border-border">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Selection Column (Left) */}
        <div className="lg:col-span-1 border-r border-border pr-4">
          <h3 className="font-medium mb-3">Select Assets</h3>

          {/* Tabs for Driver/Vehicle */}
          <div className="flex border-b border-border mb-4">
            <button
              className={`px-4 py-2 ${
                activeTab === 'vehicles'
                  ? 'border-b-2 border-primary font-medium'
                  : 'text-muted-foreground'
              }`}
              onClick={() => {
                setActiveTab('vehicles');
                setSelectedItems([]);
              }}
            >
              Vehicles
            </button>
            <button
              className={`px-4 py-2 ${
                activeTab === 'drivers'
                  ? 'border-b-2 border-primary font-medium'
                  : 'text-muted-foreground'
              }`}
              onClick={() => {
                setActiveTab('drivers');
                setSelectedItems([]);
              }}
            >
              Drivers
            </button>
          </div>

          {/* Search Input */}
          <div className="mb-4 relative">
            <input
              type="text"
              placeholder={`Search ${activeTab}...`}
              className="w-full px-4 py-2 pl-10 rounded-md border border-input bg-background text-sm"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
            <Search
              className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
              size={16}
            />
          </div>

          {/* List of selectable items */}
          <div className="max-h-64 overflow-y-auto">
            {filteredItems.length > 0 ? (
              filteredItems.map(item => (
                <div
                  key={item.id}
                  className={`p-3 border border-border rounded-md mb-2 cursor-pointer 
                    ${
                      selectedItems.some(selected => selected.id === item.id)
                        ? 'bg-accent/10'
                        : 'hover:bg-accent/10'
                    }`}
                  onClick={() => toggleSelection(item)}
                >
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-3"
                      checked={selectedItems.some(selected => selected.id === item.id)}
                      onChange={() => {}} // Handled by div click
                    />
                    <div>
                      <p className="font-medium">{item.id}</p>
                      <p className="text-sm text-muted-foreground">
                        {activeTab === 'vehicles' ? `${item.make} ${item.model}` : item.name}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center p-4 text-muted-foreground">No {activeTab} found</div>
            )}
          </div>

          {/* Date Selection */}
          <div className="mt-4">
            <h4 className="text-sm font-medium mb-2">Time Period</h4>
            <div className="flex flex-col gap-2">
              <div className="relative">
                <input
                  type="date"
                  className="px-4 py-2 pl-10 rounded-md border border-input bg-background text-sm w-full"
                  value={customDate}
                  onChange={e => setCustomDate(e.target.value)}
                />
                <Calendar
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                  size={16}
                />
              </div>
              <div className="relative">
                <select
                  className="px-4 py-2 pl-10 rounded-md border border-input bg-background text-sm w-full"
                  value={timeRange}
                  onChange={e => setTimeRange(e.target.value)}
                >
                  <option value="24h">Last 24 hours</option>
                  <option value="3d">Last 3 days</option>
                  <option value="1w">Last week</option>
                  <option value="1m">Last month</option>
                  <option value="custom">Custom range</option>
                </select>
                <Clock
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                  size={16}
                />
              </div>
            </div>
          </div>
        </div>

        {/* History Display Column (Right) */}
        <div className="lg:col-span-2">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-medium">{getHistoryTitle()}</h3>
            <div className="flex gap-2">
              <button
                className="px-3 py-1.5 bg-secondary text-secondary-foreground rounded-md text-sm flex items-center gap-1"
                onClick={exportData}
                disabled={selectedItems.length === 0}
              >
                <Download size={14} />
                Export
              </button>
              <div className="relative">
                <select
                  className="px-3 py-1.5 pl-8 rounded-md border border-input bg-background text-sm"
                  value={filterType}
                  onChange={e => setFilterType(e.target.value)}
                >
                  <option value="all">All Events</option>
                  <option value="speed">Speed Violations</option>
                  <option value="geofence">Geofence Events</option>
                  <option value="start">Start/Stop Events</option>
                  <option value="arrival">Arrivals/Departures</option>
                  <option value="idle">Idle Time</option>
                </select>
                <Filter
                  className="absolute left-2 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                  size={14}
                />
              </div>
            </div>
          </div>

          {selectedItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 text-muted-foreground">
              <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center mb-2">
                <Clock size={24} className="text-muted-foreground" />
              </div>
              <p className="text-center">
                Select a {activeTab === 'vehicles' ? 'vehicle' : 'driver'} to view location history
              </p>
            </div>
          ) : (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                <div className="p-3 bg-accent/10 rounded-md">
                  <p className="text-sm text-muted-foreground">Distance Traveled</p>
                  <p className="text-xl font-bold">187 km</p>
                </div>
                <div className="p-3 bg-accent/10 rounded-md">
                  <p className="text-sm text-muted-foreground">Avg. Speed</p>
                  <p className="text-xl font-bold">62 km/h</p>
                </div>
                <div className="p-3 bg-accent/10 rounded-md">
                  <p className="text-sm text-muted-foreground">Stops</p>
                  <p className="text-xl font-bold">12</p>
                </div>
              </div>

              {/* History Timeline */}
              <div className="border border-border rounded-md overflow-hidden">
                <div className="overflow-y-auto max-h-60">
                  {filteredHistoryData.length > 0 ? (
                    filteredHistoryData.map((event, index) => (
                      <div key={index} className="p-3 border-b border-border hover:bg-accent/10">
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-medium">{event.description}</span>
                          <span className="text-xs text-muted-foreground">{event.timestamp}</span>
                        </div>
                        <p className="text-sm text-muted-foreground">{event.location}</p>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-center text-muted-foreground">
                      No history data available for the selected filters
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default LocationHistory;
