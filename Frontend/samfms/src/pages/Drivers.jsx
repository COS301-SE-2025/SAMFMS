import React, { useState } from 'react';
import { PlusCircle } from 'lucide-react';
import DriverList from '../components/drivers/DriverList';
import DriverSearch from '../components/drivers/DriverSearch';
import DriverActions from '../components/drivers/DriverActions';
import DriverDetailsModal from '../components/drivers/DriverDetailsModal';
import VehicleAssignmentModal from '../components/drivers/VehicleAssignmentModal';
import DataVisualization from '../components/drivers/DataVisualization';

const Drivers = () => {
  const [selectedDrivers, setSelectedDrivers] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [filterOpen, setFilterOpen] = useState(false);
  const [driverDetailsOpen, setDriverDetailsOpen] = useState(false);
  const [currentDriver, setCurrentDriver] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  const [sortField, setSortField] = useState('id');
  const [sortDirection, setSortDirection] = useState('asc');
  const [showVehicleAssignmentModal, setShowVehicleAssignmentModal] = useState(false);

  // Sample driver data
  const drivers = [
    {
      id: 'DRV-001',
      name: 'John Smith',
      licenseNumber: 'DL8976543',
      phone: '(555) 123-4567',
      licenseExpiry: '2025-06-15',
      licenseType: 'Class C',
      status: 'Available',
      email: 'john.smith@example.com',
      emergencyContact: '(555) 987-6543',
      department: 'Sales',
      joiningDate: '2021-05-10',
      employeeId: 'EMP-1235',
      rating: '4.8',
      currentVehicle: {
        id: 'VEH-001',
        make: 'Toyota',
        model: 'Camry',
        licensePlate: 'ABC-1234',
      },
      trips: [
        {
          id: 'TRP-001',
          date: '2025-04-15',
          vehicle: 'Toyota Camry',
          from: 'Office HQ',
          to: 'Downtown',
          distance: '23.5 km',
          status: 'Completed',
        },
        {
          id: 'TRP-002',
          date: '2025-04-10',
          vehicle: 'Toyota Camry',
          from: 'Office HQ',
          to: 'Airport',
          distance: '45.2 km',
          status: 'Completed',
        },
        {
          id: 'TRP-003',
          date: '2025-04-02',
          vehicle: 'Toyota Camry',
          from: 'Office HQ',
          to: 'Client Site',
          distance: '12.8 km',
          status: 'Completed',
        },
      ],
      documents: [
        { id: 'DOC-001', name: 'Driver License', type: 'license', expiryDate: '2025-06-15' },
        {
          id: 'DOC-002',
          name: 'Defensive Driving Certificate',
          type: 'training',
          date: '2023-11-15',
        },
      ],
    },
    {
      id: 'DRV-002',
      name: 'Jane Wilson',
      licenseNumber: 'DL7651234',
      phone: '(555) 987-6543',
      licenseExpiry: '2026-03-22',
      licenseType: 'CDL',
      status: 'On Trip',
      email: 'jane.wilson@example.com',
      emergencyContact: '(555) 234-5678',
      department: 'Delivery',
      joiningDate: '2022-01-15',
      employeeId: 'EMP-2468',
      rating: '4.5',
      currentVehicle: {
        id: 'VEH-002',
        make: 'Ford',
        model: 'Transit',
        licensePlate: 'XYZ-5678',
      },
      trips: [
        {
          id: 'TRP-004',
          date: '2025-05-24',
          vehicle: 'Ford Transit',
          from: 'Warehouse',
          to: 'Distribution Center',
          distance: '56.7 km',
          status: 'In Progress',
        },
        {
          id: 'TRP-005',
          date: '2025-05-20',
          vehicle: 'Ford Transit',
          from: 'Warehouse',
          to: 'Retail Store',
          distance: '32.1 km',
          status: 'Completed',
        },
      ],
      documents: [
        {
          id: 'DOC-003',
          name: 'Commercial Driver License',
          type: 'license',
          expiryDate: '2026-03-22',
        },
        {
          id: 'DOC-004',
          name: 'Forklift Operation Certificate',
          type: 'training',
          date: '2024-01-10',
        },
        {
          id: 'DOC-005',
          name: 'Hazardous Materials Handling',
          type: 'training',
          date: '2024-02-05',
        },
      ],
    },
    {
      id: 'DRV-003',
      name: 'Robert Johnson',
      licenseNumber: 'DL5432198',
      phone: '(555) 456-7890',
      licenseExpiry: '2025-08-10',
      licenseType: 'Class B',
      status: 'Available',
      email: 'robert.johnson@example.com',
      emergencyContact: '(555) 345-6789',
      department: 'Operations',
      joiningDate: '2021-11-05',
      employeeId: 'EMP-3579',
      rating: '4.6',
      currentVehicle: null,
      trips: [
        {
          id: 'TRP-007',
          date: '2025-05-15',
          vehicle: 'Chevrolet Express',
          from: 'Office HQ',
          to: 'Construction Site',
          distance: '28.3 km',
          status: 'Completed',
        },
        {
          id: 'TRP-008',
          date: '2025-05-12',
          vehicle: 'Chevrolet Express',
          from: 'Office HQ',
          to: 'Warehouse',
          distance: '15.6 km',
          status: 'Completed',
        },
      ],
      documents: [
        {
          id: 'DOC-006',
          name: 'Driver License Class B',
          type: 'license',
          expiryDate: '2025-08-10',
        },
        { id: 'DOC-007', name: 'First Aid Certificate', type: 'training', date: '2023-09-20' },
      ],
    },
    {
      id: 'DRV-004',
      name: 'Emily Davis',
      licenseNumber: 'DL3219876',
      phone: '(555) 789-0123',
      licenseExpiry: '2025-11-05',
      licenseType: 'Class A',
      status: 'On Leave',
      email: 'emily.davis@example.com',
      emergencyContact: '(555) 456-7890',
      department: 'Executive',
      joiningDate: '2020-06-22',
      employeeId: 'EMP-4680',
      rating: '4.9',
      currentVehicle: {
        id: 'VEH-004',
        make: 'Tesla',
        model: 'Model 3',
        licensePlate: 'GHI-3456',
      },
      trips: [
        {
          id: 'TRP-010',
          date: '2025-04-30',
          vehicle: 'Tesla Model 3',
          from: 'Office HQ',
          to: 'Conference Center',
          distance: '18.2 km',
          status: 'Completed',
        },
        {
          id: 'TRP-011',
          date: '2025-04-28',
          vehicle: 'Tesla Model 3',
          from: 'Office HQ',
          to: 'Airport',
          distance: '45.2 km',
          status: 'Completed',
        },
      ],
      documents: [
        {
          id: 'DOC-008',
          name: 'Commercial Driver License Class A',
          type: 'license',
          expiryDate: '2025-11-05',
        },
        { id: 'DOC-009', name: 'Executive Driver Training', type: 'training', date: '2023-07-15' },
      ],
    },
    {
      id: 'DRV-005',
      name: 'Michael Brown',
      licenseNumber: 'DL9876543',
      phone: '(555) 234-5678',
      licenseExpiry: '2025-05-30',
      licenseType: 'Class C',
      status: 'Inactive',
      email: 'michael.brown@example.com',
      emergencyContact: '(555) 678-9012',
      department: 'Support',
      joiningDate: '2022-03-10',
      employeeId: 'EMP-5791',
      rating: '3.8',
      currentVehicle: null,
      trips: [],
      documents: [
        { id: 'DOC-010', name: 'Driver License', type: 'license', expiryDate: '2025-05-30' },
      ],
    },
  ];

  // Sorting function
  const handleSort = field => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Sort drivers based on current sort field and direction
  const sortedDrivers = [...drivers].sort((a, b) => {
    // Standard string comparison
    if (a[sortField] < b[sortField]) return sortDirection === 'asc' ? -1 : 1;
    if (a[sortField] > b[sortField]) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  // Get current drivers for pagination
  const indexOfLastDriver = currentPage * itemsPerPage;
  const indexOfFirstDriver = indexOfLastDriver - itemsPerPage;
  const currentDrivers = sortedDrivers.slice(indexOfFirstDriver, indexOfLastDriver);
  const totalPages = Math.ceil(drivers.length / itemsPerPage);

  // Toggle select all
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedDrivers([]);
    } else {
      setSelectedDrivers(currentDrivers.map(driver => driver.id));
    }
    setSelectAll(!selectAll);
  };

  // Toggle select individual driver
  const handleSelectDriver = driverId => {
    if (selectedDrivers.includes(driverId)) {
      setSelectedDrivers(selectedDrivers.filter(id => id !== driverId));
    } else {
      setSelectedDrivers([...selectedDrivers, driverId]);
    }
  };

  // Open driver details
  const openDriverDetails = driver => {
    setCurrentDriver(driver);
    setDriverDetailsOpen(true);
  };

  // Close driver details
  const closeDriverDetails = () => {
    setDriverDetailsOpen(false);
    setCurrentDriver(null);
  };

  // Open vehicle assignment modal
  const openVehicleAssignmentModal = () => {
    setShowVehicleAssignmentModal(true);
  };

  // Close vehicle assignment modal
  const closeVehicleAssignmentModal = () => {
    setShowVehicleAssignmentModal(false);
  };

  // Export selected drivers
  const exportSelectedDrivers = () => {
    const selectedData = drivers.filter(driver => selectedDrivers.includes(driver.id));
    // In a real app, this would create a CSV or Excel file
    console.log('Exporting data for:', selectedData);
    alert(`Exporting data for ${selectedData.length} drivers`);
  };

  // Pagination handlers
  const goToNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages));
  };

  const goToPrevPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1));
  };

  const changeItemsPerPage = e => {
    setItemsPerPage(parseInt(e.target.value));
    setCurrentPage(1); // Reset to first page
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Fleet Drivers</h1>
      <div className="bg-card rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Manage Drivers</h2>
          <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition flex items-center gap-2">
            <PlusCircle size={18} />
            <span>Add Driver</span>
          </button>
        </div>

        {/* Search and filter bar */}
        <DriverSearch
          filterOpen={filterOpen}
          setFilterOpen={setFilterOpen}
          onSearch={() => {}}
          onApplyFilters={() => setFilterOpen(false)}
          onResetFilters={() => setFilterOpen(false)}
        />

        {/* Driver actions */}
        <DriverActions
          selectedDrivers={selectedDrivers}
          exportSelectedDrivers={exportSelectedDrivers}
        />

        {/* Driver list with pagination */}
        <DriverList
          drivers={currentDrivers}
          selectedDrivers={selectedDrivers}
          handleSelectDriver={handleSelectDriver}
          selectAll={selectAll}
          handleSelectAll={handleSelectAll}
          sortField={sortField}
          sortDirection={sortDirection}
          handleSort={handleSort}
          openDriverDetails={openDriverDetails}
          currentPage={currentPage}
          totalPages={totalPages}
          itemsPerPage={itemsPerPage}
          changeItemsPerPage={changeItemsPerPage}
          goToNextPage={goToNextPage}
          goToPrevPage={goToPrevPage}
        />
      </div>

      {/* Driver Details Modal */}
      {driverDetailsOpen && currentDriver && (
        <DriverDetailsModal
          driver={currentDriver}
          closeDriverDetails={closeDriverDetails}
          openVehicleAssignmentModal={openVehicleAssignmentModal}
        />
      )}

      {/* Vehicle Assignment Modal */}
      {showVehicleAssignmentModal && (
        <VehicleAssignmentModal
          closeVehicleAssignmentModal={closeVehicleAssignmentModal}
          selectedDrivers={selectedDrivers}
          currentDriver={currentDriver}
        />
      )}

      {/* Data visualization section */}
      <DataVisualization />
    </div>
  );
};

export default Drivers;
