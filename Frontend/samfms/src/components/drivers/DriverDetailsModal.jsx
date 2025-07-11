import React, { useState } from 'react';
import { X, UserCog, Car, FileText } from 'lucide-react';
import StatusBadge from '../vehicles/StatusBadge';

const DriverDetailsModal = ({ driver, closeDriverDetails, openVehicleAssignmentModal }) => {
  const [activeTab, setActiveTab] = useState('overview');

  const getStatusColor = status => {
    const statusMap = {
      available: 'success',
      onTrip: 'info',
      onLeave: 'warning',
      inactive: 'destructive',
    };
    return statusMap[status.toLowerCase().replace(/\s+/g, '')] || 'default';
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-auto animate-in fade-in-0 zoom-in-95">
        <div className="sticky top-0 bg-background z-10 p-4 border-b border-border flex items-center justify-between">
          <h2 className="text-2xl font-bold">{driver.name}</h2>
          <button onClick={closeDriverDetails} className="hover:bg-muted rounded-full p-1">
            <X size={24} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-b-2 border-primary text-primary'
                : 'text-muted-foreground'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('trips')}
            className={`px-4 py-2 font-medium text-sm ${
              activeTab === 'trips'
                ? 'border-b-2 border-primary text-primary'
                : 'text-muted-foreground'
            }`}
          >
            Trip History
          </button>
          <button
            onClick={() => setActiveTab('docs')}
            className={`px-4 py-2 font-medium text-sm ${
              activeTab === 'docs'
                ? 'border-b-2 border-primary text-primary'
                : 'text-muted-foreground'
            }`}
          >
            Documents
          </button>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="col-span-2">
                <div className="flex items-center mb-6">
                  <div className="w-20 h-20 bg-muted rounded-full flex items-center justify-center text-3xl font-bold mr-4">
                    {driver.name
                      .split(' ')
                      .map(name => name[0])
                      .join('')}
                  </div>{' '}
                  <div>
                    <h3 className="text-xl font-bold">{driver.name}</h3>
                    <p className="text-muted-foreground">Employee ID: {driver.employeeId}</p>
                    <StatusBadge status={driver.status} type={getStatusColor(driver.status)} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="border border-border rounded-md p-4">
                    <h4 className="font-medium mb-2 text-sm text-muted-foreground">
                      Contact Information
                    </h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Phone:</span>
                        <span className="font-medium">{driver.phone}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Email:</span>
                        <span className="font-medium">{driver.email}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Emergency Contact:</span>
                        <span className="font-medium">{driver.emergencyContact}</span>
                      </div>
                    </div>
                  </div>

                  <div className="border border-border rounded-md p-4">
                    <h4 className="font-medium mb-2 text-sm text-muted-foreground">
                      License Information
                    </h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>License Number:</span>
                        <span className="font-medium">{driver.licenseNumber}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>License Type:</span>
                        <span className="font-medium">{driver.licenseType}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Expiry Date:</span>
                        <span className="font-medium">{driver.licenseExpiry}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="border border-border rounded-md p-4">
                  <h4 className="font-medium mb-2 text-sm text-muted-foreground">
                    Current Assignment
                  </h4>
                  {driver.currentVehicle ? (
                    <div className="flex items-center">
                      <Car className="mr-2" size={18} />
                      <div>
                        <p className="font-medium">
                          {driver.currentVehicle.make} {driver.currentVehicle.model}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {driver.currentVehicle.id} • {driver.currentVehicle.licensePlate}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center">
                      <p className="text-muted-foreground">No vehicle currently assigned</p>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <div className="border border-border rounded-md p-4 mb-6">
                  <h4 className="font-medium mb-2 text-sm text-muted-foreground">
                    Driver Information
                  </h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Department:</span>
                      <span className="font-medium">{driver.department}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Joining Date:</span>
                      <span className="font-medium">{driver.joiningDate}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Employee ID:</span>
                      <span className="font-medium">{driver.employeeId}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Driver Rating:</span>
                      <span className="font-medium">{driver.rating}/5</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col space-y-2">
                  <button
                    onClick={openVehicleAssignmentModal}
                    className="w-full py-2 px-4 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 flex items-center justify-center gap-2"
                  >
                    <Car size={18} />
                    Assign Vehicle
                  </button>
                  <button className="w-full py-2 px-4 border border-input rounded-md hover:bg-accent hover:text-accent-foreground flex items-center justify-center gap-2">
                    <UserCog size={18} />
                    Edit Driver
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Trips Tab */}
          {activeTab === 'trips' && (
            <div>
              <h3 className="text-xl font-bold mb-4">Trip History</h3>
              <div className="border border-border rounded-md overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="px-4 py-3 text-left">Trip ID</th>
                      <th className="px-4 py-3 text-left">Date</th>
                      <th className="px-4 py-3 text-left">Vehicle</th>
                      <th className="px-4 py-3 text-left">From</th>
                      <th className="px-4 py-3 text-left">To</th>
                      <th className="px-4 py-3 text-left">Distance</th>
                      <th className="px-4 py-3 text-left">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {driver.trips?.map(trip => (
                      <tr key={trip.id} className="border-t border-border hover:bg-accent/10">
                        <td className="px-4 py-3">{trip.id}</td>
                        <td className="px-4 py-3">{trip.date}</td>
                        <td className="px-4 py-3">{trip.vehicle}</td>
                        <td className="px-4 py-3">{trip.from}</td>
                        <td className="px-4 py-3">{trip.to}</td>
                        <td className="px-4 py-3">{trip.distance}</td>
                        <td className="px-4 py-3">
                          <StatusBadge
                            status={trip.status}
                            type={trip.status.toLowerCase() === 'completed' ? 'success' : 'info'}
                          />
                        </td>
                      </tr>
                    ))}
                    {(!driver.trips || driver.trips.length === 0) && (
                      <tr>
                        <td colSpan="7" className="px-4 py-3 text-center text-muted-foreground">
                          No trip history available
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Documents Tab */}
          {activeTab === 'docs' && (
            <div>
              <h3 className="text-xl font-bold mb-4">Driver Documents</h3>
              <div className="border border-border rounded-md p-4 mb-4">
                <div className="flex justify-between items-center mb-4">
                  <h4 className="font-medium">License & Certificates</h4>
                  <button className="text-sm text-primary">Upload New</button>
                </div>
                <div className="space-y-2">
                  {driver.documents
                    ?.filter(doc => doc.type === 'license')
                    ?.map(doc => (
                      <div
                        key={doc.id}
                        className="flex items-center justify-between p-2 border border-border rounded-md"
                      >
                        <div className="flex items-center">
                          <FileText size={18} className="mr-2 text-muted-foreground" />
                          <div>
                            <p className="font-medium">{doc.name}</p>
                            <p className="text-xs text-muted-foreground">
                              Expires: {doc.expiryDate}
                            </p>
                          </div>
                        </div>
                        <button className="text-primary text-sm">View</button>
                      </div>
                    ))}
                </div>
              </div>

              <div className="border border-border rounded-md p-4">
                <div className="flex justify-between items-center mb-4">
                  <h4 className="font-medium">Training Records</h4>
                  <button className="text-sm text-primary">Upload New</button>
                </div>
                <div className="space-y-2">
                  {driver.documents
                    ?.filter(doc => doc.type === 'training')
                    ?.map(doc => (
                      <div
                        key={doc.id}
                        className="flex items-center justify-between p-2 border border-border rounded-md"
                      >
                        <div className="flex items-center">
                          <FileText size={18} className="mr-2 text-muted-foreground" />
                          <div>
                            <p className="font-medium">{doc.name}</p>
                            <p className="text-xs text-muted-foreground">Completed: {doc.date}</p>
                          </div>
                        </div>
                        <button className="text-primary text-sm">View</button>
                      </div>
                    ))}
                  {(!driver.documents ||
                    driver.documents.filter(doc => doc.type === 'training').length === 0) && (
                    <p className="text-muted-foreground text-sm">No training records available</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DriverDetailsModal;
