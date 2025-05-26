import React, { useState } from 'react';
import { PlusCircle } from 'lucide-react';
import VehicleList from '../components/vehicles/VehicleList';
import VehicleSearch from '../components/vehicles/VehicleSearch';
import VehicleActions from '../components/vehicles/VehicleActions';
import VehicleDetailsModal from '../components/vehicles/VehicleDetailsModal';
import DriverAssignmentModal from '../components/vehicles/DriverAssignmentModal';
import DataVisualization from '../components/vehicles/DataVisualization';

const Vehicles = () => {
  const [selectedVehicles, setSelectedVehicles] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [filterOpen, setFilterOpen] = useState(false);
  const [vehicleDetailsOpen, setVehicleDetailsOpen] = useState(false);
  const [currentVehicle, setCurrentVehicle] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  const [sortField, setSortField] = useState('id');
  const [sortDirection, setSortDirection] = useState('asc');
  const [showAssignmentModal, setShowAssignmentModal] = useState(false);
  // Sample data
  const vehicles = [
    {
      id: 'VEH-001',
      make: 'Toyota',
      model: 'Camry',
      year: '2023',
      mileage: '15,430',
      driver: 'John Doe',
      status: 'Active',
      vin: 'JT2BF22K1W0158036',
      licensePlate: 'ABC-1234',
      fuelType: 'Hybrid',
      department: 'Sales',
      lastService: '2023-09-15',
      nextService: '2024-03-15',
      fuelEfficiency: '52 mpg',
      tags: ['Executive', 'Sales', 'East Region'],
      acquisitionDate: '2023-01-15',
      insuranceExpiry: '2024-01-15',
      lastDriver: 'Emily White',
      maintenanceCosts: [
        { date: '2023-03-10', cost: 120, type: 'Oil Change' },
        { date: '2023-06-20', cost: 85, type: 'Tire Rotation' },
        { date: '2023-09-15', cost: 350, type: 'Brake Service' },
      ],
    },
    {
      id: 'VEH-002',
      make: 'Ford',
      model: 'Transit',
      year: '2022',
      mileage: '28,745',
      driver: 'Emma Johnson',
      status: 'Maintenance',
      vin: '1FTYR10D98PA22005',
      licensePlate: 'XYZ-5678',
      fuelType: 'Diesel',
      department: 'Delivery',
      lastService: '2023-08-20',
      nextService: '2024-02-20',
      fuelEfficiency: '24 mpg',
      tags: ['Delivery', 'North Region', 'High Mileage'],
      acquisitionDate: '2022-03-10',
      insuranceExpiry: '2024-03-10',
      lastDriver: 'James Wilson',
      maintenanceCosts: [
        { date: '2022-06-15', cost: 150, type: 'Oil Change' },
        { date: '2022-10-05', cost: 280, type: 'Tire Replacement' },
        { date: '2023-02-18', cost: 420, type: 'Major Service' },
        { date: '2023-08-20', cost: 1200, type: 'Transmission Repair' },
      ],
    },
    {
      id: 'VEH-003',
      make: 'Honda',
      model: 'Civic',
      year: '2021',
      mileage: '32,120',
      driver: 'Michael Smith',
      status: 'Active',
      vin: '19XFC2F59NE002281',
      licensePlate: 'DEF-9012',
      fuelType: 'Gasoline',
      department: 'Support',
      lastService: '2023-10-05',
      nextService: '2024-04-05',
      fuelEfficiency: '38 mpg',
      tags: ['Support', 'Field Tech', 'West Region'],
      acquisitionDate: '2021-11-22',
      insuranceExpiry: '2024-11-22',
      lastDriver: 'Michael Smith',
      maintenanceCosts: [
        { date: '2022-05-12', cost: 95, type: 'Oil Change' },
        { date: '2022-11-30', cost: 210, type: 'Brake Service' },
        { date: '2023-04-22', cost: 150, type: 'General Inspection' },
        { date: '2023-10-05', cost: 320, type: 'Major Service' },
      ],
    },
    {
      id: 'VEH-004',
      make: 'Tesla',
      model: 'Model 3',
      year: '2023',
      mileage: '8,215',
      driver: 'Sarah Davis',
      status: 'Active',
      vin: '5YJ3E1EA0PF290559',
      licensePlate: 'GHI-3456',
      fuelType: 'Electric',
      department: 'Executive',
      lastService: '2023-11-10',
      nextService: '2024-05-10',
      fuelEfficiency: '132 MPGe',
      tags: ['Executive', 'Low Emissions', 'South Region'],
      acquisitionDate: '2023-05-18',
      insuranceExpiry: '2024-05-18',
      lastDriver: 'Sarah Davis',
      maintenanceCosts: [
        { date: '2023-08-15', cost: 180, type: 'Tire Rotation' },
        { date: '2023-11-10', cost: 250, type: 'Software Update & Inspection' },
      ],
    },
    {
      id: 'VEH-005',
      make: 'Chevrolet',
      model: 'Silverado',
      year: '2021',
      mileage: '45,670',
      driver: 'Unassigned',
      status: 'Maintenance',
      vin: '1GCUYAEF8MZ145263',
      licensePlate: 'JKL-7890',
      fuelType: 'Gasoline',
      department: 'Construction',
      lastService: '2023-07-25',
      nextService: '2024-01-25',
      fuelEfficiency: '20 mpg',
      tags: ['Construction', 'Heavy Duty', 'Central Region'],
      acquisitionDate: '2021-09-05',
      insuranceExpiry: '2024-09-05',
      lastDriver: 'Robert Brown',
      maintenanceCosts: [
        { date: '2022-03-18', cost: 160, type: 'Oil Change' },
        { date: '2022-09-30', cost: 380, type: 'Suspension Repair' },
        { date: '2023-01-15', cost: 220, type: 'Electrical System' },
        { date: '2023-07-25', cost: 1450, type: 'Engine Repair' },
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

  // Sort vehicles based on current sort field and direction
  const sortedVehicles = [...vehicles].sort((a, b) => {
    if (sortField === 'mileage') {
      // Convert to numbers for proper comparison
      const aNum = parseInt(a[sortField].replace(/,/g, ''));
      const bNum = parseInt(b[sortField].replace(/,/g, ''));
      return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
    } else {
      // Standard string comparison
      if (a[sortField] < b[sortField]) return sortDirection === 'asc' ? -1 : 1;
      if (a[sortField] > b[sortField]) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    }
  });

  // Get current vehicles for pagination
  const indexOfLastVehicle = currentPage * itemsPerPage;
  const indexOfFirstVehicle = indexOfLastVehicle - itemsPerPage;
  const currentVehicles = sortedVehicles.slice(indexOfFirstVehicle, indexOfLastVehicle);
  const totalPages = Math.ceil(vehicles.length / itemsPerPage);

  // Sorting is now handled in the VehicleList component

  // Toggle select all (update to use currentVehicles)
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedVehicles([]);
    } else {
      setSelectedVehicles(currentVehicles.map(vehicle => vehicle.id));
    }
    setSelectAll(!selectAll);
  };

  // Toggle select individual vehicle
  const handleSelectVehicle = vehicleId => {
    if (selectedVehicles.includes(vehicleId)) {
      setSelectedVehicles(selectedVehicles.filter(id => id !== vehicleId));
    } else {
      setSelectedVehicles([...selectedVehicles, vehicleId]);
    }
  };

  // Open vehicle details
  const openVehicleDetails = vehicle => {
    setCurrentVehicle(vehicle);
    setVehicleDetailsOpen(true);
  };

  // Close vehicle details
  const closeVehicleDetails = () => {
    setVehicleDetailsOpen(false);
    setCurrentVehicle(null);
  };

  // Open vehicle assignment modal
  const openAssignmentModal = () => {
    setShowAssignmentModal(true);
  };

  // Close vehicle assignment modal
  const closeAssignmentModal = () => {
    setShowAssignmentModal(false);
  };
  // Analytics are always shown now

  // Bulk operations
  const exportSelectedVehicles = () => {
    const selectedData = vehicles.filter(vehicle => selectedVehicles.includes(vehicle.id));
    // In a real app, this would create a CSV or Excel file
    console.log('Exporting data for:', selectedData);
    alert(`Exporting data for ${selectedData.length} vehicles`);
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
      <h1 className="text-3xl font-bold mb-6">Fleet Vehicles</h1>
      <div className="bg-card rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Manage Vehicles</h2>
          <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition flex items-center gap-2">
            <PlusCircle size={18} />
            <span>Add Vehicle</span>
          </button>
        </div>
        {/* Search and filter bar */}
        <VehicleSearch
          filterOpen={filterOpen}
          setFilterOpen={setFilterOpen}
          onSearch={() => {}}
          onApplyFilters={() => setFilterOpen(false)}
          onResetFilters={() => setFilterOpen(false)}
        />{' '}
        {/* Vehicle actions buttons and bulk actions */}
        <VehicleActions
          selectedVehicles={selectedVehicles}
          openAssignmentModal={openAssignmentModal}
          exportSelectedVehicles={exportSelectedVehicles}
        />{' '}
        {/* Vehicle list with pagination */}
        <VehicleList
          vehicles={currentVehicles}
          selectedVehicles={selectedVehicles}
          handleSelectVehicle={handleSelectVehicle}
          selectAll={selectAll}
          handleSelectAll={handleSelectAll}
          sortField={sortField}
          sortDirection={sortDirection}
          handleSort={handleSort}
          openVehicleDetails={openVehicleDetails}
          currentPage={currentPage}
          totalPages={totalPages}
          itemsPerPage={itemsPerPage}
          changeItemsPerPage={changeItemsPerPage}
          goToNextPage={goToNextPage}
          goToPrevPage={goToPrevPage}
        />
      </div>{' '}
      {/* Vehicle Details Modal */}
      {vehicleDetailsOpen && currentVehicle && (
        <VehicleDetailsModal
          vehicle={currentVehicle}
          closeVehicleDetails={closeVehicleDetails}
          openAssignmentModal={openAssignmentModal}
        />
      )}{' '}
      {/* Driver Assignment Modal */}
      {showAssignmentModal && (
        <DriverAssignmentModal
          closeAssignmentModal={closeAssignmentModal}
          selectedVehicles={selectedVehicles}
          handleSelectVehicle={handleSelectVehicle}
          vehicles={vehicles}
          currentVehicle={currentVehicle}
        />
      )}{' '}
      {/* Data visualization section */}
      <DataVisualization />
    </div>
  );
};

export default Vehicles;
