import React, { useState, useEffect } from 'react';
import { X, Car, Hash, CreditCard } from 'lucide-react';
import { updateVehicle } from '../../backend/API';
import ColorDropdown from './ColorDropdown';
import CustomDropdown from './CustomDropdown';

// South African popular vehicle makes and models
const southAfricanVehicles = {
  Toyota: [
    'Hilux',
    'Corolla',
    'Fortuner',
    'Quantum',
    'Avanza',
    'Urban Cruiser',
    'C-HR',
    'Prius',
    'Camry',
    'Land Cruiser',
  ],
  Volkswagen: [
    'Polo',
    'Golf',
    'Tiguan',
    'Amarok',
    'Jetta',
    'Passat',
    'T-Cross',
    'Touareg',
    'Arteon',
    'Caddy',
  ],
  Ford: ['Ranger', 'EcoSport', 'Focus', 'Fiesta', 'Kuga', 'Everest', 'Mustang', 'Territory'],
  BMW: [
    '1 Series',
    '2 Series',
    '3 Series',
    '4 Series',
    '5 Series',
    '7 Series',
    'X1',
    'X3',
    'X5',
    'X7',
  ],
  Mercedes: [
    'A-Class',
    'B-Class',
    'C-Class',
    'E-Class',
    'S-Class',
    'GLA',
    'GLC',
    'GLE',
    'G-Class',
    'Sprinter',
  ],
  Audi: ['A1', 'A3', 'A4', 'A6', 'Q2', 'Q3', 'Q5', 'Q7', 'Q8', 'TT'],
  Nissan: ['Micra', 'Almera', 'Sentra', 'Qashqai', 'X-Trail', 'Patrol', 'Navara', 'NP200', 'NP300'],
  Hyundai: ['i10', 'i20', 'Accent', 'Elantra', 'Tucson', 'Santa Fe', 'Creta', 'H100', 'H1'],
  Kia: ['Picanto', 'Rio', 'Cerato', 'Seltos', 'Sportage', 'Sorento', 'Carnival', 'Stinger'],
  Mazda: ['Mazda2', 'Mazda3', 'CX-3', 'CX-5', 'CX-9', 'BT-50'],
  Chevrolet: ['Spark', 'Aveo', 'Cruze', 'Captiva', 'Trailblazer', 'Utility'],
  Renault: ['Kwid', 'Sandero', 'Duster', 'Captur', 'Koleos', 'Triber'],
  Peugeot: ['108', '208', '2008', '3008', '5008', 'Partner'],
  Isuzu: ['D-Max', 'MU-X', 'KB', 'NPR', 'FTR'],
  Mitsubishi: ['Mirage', 'ASX', 'Outlander', 'Pajero', 'Triton'],
  Suzuki: ['Swift', 'Baleno', 'Vitara', 'S-Presso', 'Ertiga', 'Jimny'],
  Mahindra: ['KUV100', 'XUV300', 'XUV500', 'Scorpio', 'Bolero', 'Pik Up'],
  Tata: ['Indica', 'Indigo', 'Safari', 'Xenon', 'Super Ace'],
  Other: ['Custom Make'],
};

const vehicleColors = [
  'White',
  'Black',
  'Silver',
  'Grey',
  'Blue',
  'Red',
  'Green',
  'Yellow',
  'Orange',
  'Brown',
  'Beige',
  'Gold',
  'Purple',
  'Pink',
  'Maroon',
  'Navy',
  'Specify',
];

// Color mapping for visual circles
const colorMap = {
  White: '#ffffff',
  Black: '#000000',
  Silver: '#c0c0c0',
  Grey: '#808080',
  Blue: '#0000ff',
  Red: '#ff0000',
  Green: '#008000',
  Yellow: '#ffff00',
  Orange: '#ffa500',
  Brown: '#a52a2a',
  Beige: '#f5f5dc',
  Gold: '#ffd700',
  Purple: '#800080',
  Pink: '#ffc0cb',
  Maroon: '#800000',
  Navy: '#000080',
};

const EditVehicleModal = ({ vehicle, closeModal, onVehicleUpdated }) => {
  const [form, setForm] = useState({
    make: '',
    model: '',
    year: '',
    vin: '',
    license_plate: '',
    color: '',
    fuel_type: '',
    mileage: '',
    status: '',
    customMake: '',
    customModel: '',
    customColor: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Validation errors state
  const [validationErrors, setValidationErrors] = useState({});

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: currentYear - 1980 + 1 }, (_, i) => currentYear - i);

  // Validate individual fields
  const validateField = (name, value) => {
    const errors = { ...validationErrors };

    switch (name) {
      case 'vin':
        if (value && value.length !== 17) {
          errors.vin = 'VIN must be exactly 17 characters';
        } else {
          delete errors.vin;
        }
        break;
      case 'license_plate':
        if (value && (value.length < 4 || value.length > 10)) {
          errors.license_plate = 'License plate must be 4-10 characters';
        } else {
          delete errors.license_plate;
        }
        break;
      case 'year':
        if (value) {
          const yearValue = parseInt(value);
          if (isNaN(yearValue) || yearValue < 1980 || yearValue > currentYear + 1) {
            errors.year = `Year must be between 1980 and ${currentYear + 1}`;
          } else {
            delete errors.year;
          }
        }
        break;
      case 'customMake':
        if (form.make === 'Specify' && !value.trim()) {
          errors.customMake = 'Please specify a custom make';
        } else {
          delete errors.customMake;
        }
        break;
      case 'customModel':
        if (form.model === 'Specify' && !value.trim()) {
          errors.customModel = 'Please specify a custom model';
        } else {
          delete errors.customModel;
        }
        break;
      case 'customColor':
        if (form.color === 'Specify' && !value.trim()) {
          errors.customColor = 'Please specify a custom color';
        } else {
          delete errors.customColor;
        }
        break;
      default:
        break;
    }

    setValidationErrors(errors);
  };

  // Initialize form with vehicle data
  useEffect(() => {
    if (vehicle) {
      // Determine if this is a custom make/model/color
      const isCustomMake = !Object.keys(southAfricanVehicles).includes(vehicle.make);
      const isCustomModel =
        vehicle.make &&
        southAfricanVehicles[vehicle.make] &&
        !southAfricanVehicles[vehicle.make].includes(vehicle.model);
      const isCustomColor = !vehicleColors.filter(c => c !== 'Specify').includes(vehicle.color);

      setForm({
        make: isCustomMake ? 'Specify' : vehicle.make || '',
        model: isCustomModel ? 'Specify' : vehicle.model || '',
        year: vehicle.year || '',
        vin: vehicle.vin || '',
        license_plate: vehicle.licensePlate || '',
        color: isCustomColor ? 'Specify' : vehicle.color || '',
        fuel_type: vehicle.fuelType === 'gasoline' ? 'petrol' : vehicle.fuelType || '',
        mileage: vehicle.mileage ? parseInt(vehicle.mileage) : 0,
        status: vehicle.status?.toLowerCase() || 'active',
        customMake: isCustomMake ? vehicle.make : '',
        customModel: isCustomModel ? vehicle.model : '',
        customColor: isCustomColor ? vehicle.color : '',
      });
    }
  }, [vehicle]);
  const handleChange = e => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));

    // Validate the field
    validateField(name, value);

    // Reset custom fields when switching from "Specify" to specific option
    if (name === 'make' && value !== 'Specify') {
      setForm(prev => ({ ...prev, customMake: '', model: '', customModel: '' }));
      validateField('customMake', '');
    }
    if (name === 'model' && value !== 'Specify') {
      setForm(prev => ({ ...prev, customModel: '' }));
      validateField('customModel', '');
    }
    if (name === 'color' && value !== 'Specify') {
      setForm(prev => ({ ...prev, customColor: '' }));
      validateField('customColor', '');
    }
  };

  const getAvailableModels = () => {
    if (form.make === 'Specify') {
      return ['Specify'];
    }
    const models = southAfricanVehicles[form.make] || [];
    return [...models, 'Specify'];
  };

  const getFinalMake = () => {
    return form.make === 'Specify' ? form.customMake : form.make;
  };

  const getFinalModel = () => {
    return form.model === 'Specify' ? form.customModel : form.model;
  };

  const getFinalColor = () => {
    return form.color === 'Specify' ? form.customColor : form.color;
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      // Get final values (custom or selected)
      const finalMake = getFinalMake();
      const finalModel = getFinalModel();
      const finalColor = getFinalColor();

      // Validate required fields
      if (!finalMake || !finalModel || !form.year || !form.vin || !form.license_plate) {
        throw new Error('Please fill in all required fields');
      }

      // Validate VIN (should be 17 characters)
      if (form.vin && form.vin.length !== 17) {
        throw new Error('VIN must be exactly 17 characters');
      }

      // Validate license plate
      if (form.license_plate && (form.license_plate.length < 4 || form.license_plate.length > 10)) {
        throw new Error('License plate must be 4-10 characters');
      }

      // Validate year
      const yearValue = parseInt(form.year);
      if (isNaN(yearValue) || yearValue < 1980 || yearValue > currentYear + 1) {
        throw new Error(`Year must be between 1980 and ${currentYear + 1}`);
      }

      // Convert and prepare form data
      const formData = {
        make: finalMake,
        model: finalModel,
        color: finalColor,
        year: parseInt(form.year),
        mileage: parseInt(form.mileage),
        vin: form.vin,
        license_plate: form.license_plate,
        fuel_type: form.fuel_type,
        status: form.status,
      };

      const response = await updateVehicle(vehicle.id, formData);
      onVehicleUpdated(response);
      closeModal();
    } catch (err) {
      console.error('Error updating vehicle:', err);
      setError(err.message || 'Failed to update vehicle');
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card p-6 rounded-lg shadow-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-card-foreground">Edit Vehicle</h2>
          <button onClick={closeModal} className="text-muted-foreground hover:text-foreground">
            <X size={24} />
          </button>
        </div>

        {error && (
          <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Vehicle Information */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Car size={20} />
              Vehicle Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {' '}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Make <span className="text-destructive">*</span>
                </label>
                {validationErrors.make && (
                  <div className="text-destructive text-sm mb-1">{validationErrors.make}</div>
                )}{' '}
                <CustomDropdown
                  value={form.make}
                  onChange={value => handleChange({ target: { name: 'make', value } })}
                  options={[
                    { value: 'Specify', label: 'Specify' },
                    ...Object.keys(southAfricanVehicles)
                      .filter(make => make !== 'Other')
                      .map(make => ({ value: make, label: make })),
                  ]}
                  placeholder="Select Make"
                  maxVisibleOptions={5}
                />
                {form.make === 'Specify' && (
                  <>
                    {validationErrors.customMake && (
                      <div className="text-destructive text-sm mb-1 mt-1">
                        {validationErrors.customMake}
                      </div>
                    )}
                    <input
                      type="text"
                      name="customMake"
                      value={form.customMake}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-input rounded-md bg-background mt-2"
                      placeholder="Enter custom make"
                    />
                  </>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Model <span className="text-destructive">*</span>
                </label>
                {validationErrors.model && (
                  <div className="text-destructive text-sm mb-1">{validationErrors.model}</div>
                )}{' '}
                <CustomDropdown
                  value={form.model}
                  onChange={value => handleChange({ target: { name: 'model', value } })}
                  options={
                    form.make
                      ? getAvailableModels().map(model => ({ value: model, label: model }))
                      : []
                  }
                  placeholder="Select Model"
                  disabled={!form.make}
                  maxVisibleOptions={5}
                />
                {form.model === 'Specify' && (
                  <>
                    {validationErrors.customModel && (
                      <div className="text-destructive text-sm mb-1 mt-1">
                        {validationErrors.customModel}
                      </div>
                    )}
                    <input
                      type="text"
                      name="customModel"
                      value={form.customModel}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-input rounded-md bg-background mt-2"
                      placeholder="Enter custom model"
                    />
                  </>
                )}
              </div>{' '}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Year <span className="text-destructive">*</span>
                </label>
                {validationErrors.year && (
                  <div className="text-destructive text-sm mb-1">{validationErrors.year}</div>
                )}{' '}
                <CustomDropdown
                  value={form.year}
                  onChange={value => handleChange({ target: { name: 'year', value } })}
                  options={years.map(year => ({ value: year.toString(), label: year.toString() }))}
                  placeholder="Select Year"
                  maxVisibleOptions={5}
                />
              </div>{' '}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Color <span className="text-destructive">*</span>
                </label>
                {validationErrors.color && (
                  <div className="text-destructive text-sm mb-1">{validationErrors.color}</div>
                )}{' '}
                <ColorDropdown
                  value={form.color}
                  onChange={value => handleChange({ target: { name: 'color', value } })}
                  colors={vehicleColors}
                  colorMap={colorMap}
                  placeholder="Select Color"
                />
                {form.color === 'Specify' && (
                  <>
                    {validationErrors.customColor && (
                      <div className="text-destructive text-sm mb-1 mt-1">
                        {validationErrors.customColor}
                      </div>
                    )}
                    <input
                      type="text"
                      name="customColor"
                      value={form.customColor}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-input rounded-md bg-background mt-2"
                      placeholder="Enter custom color"
                    />
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Technical Information */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Hash size={20} />
              Technical Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {' '}
              <div>
                <label className="block text-sm font-medium mb-2">
                  VIN <span className="text-destructive">*</span>
                </label>
                {validationErrors.vin && (
                  <div className="text-destructive text-sm mb-1">{validationErrors.vin}</div>
                )}
                <input
                  type="text"
                  name="vin"
                  value={form.vin}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-input rounded-md bg-background"
                  placeholder="17-character VIN"
                  maxLength="17"
                  minLength="17"
                  required
                />
                <p className="text-xs text-muted-foreground mt-1">
                  17 character Vehicle Identification Number
                </p>
              </div>{' '}
              <div>
                <label className="block text-sm font-medium mb-2">
                  License Plate <span className="text-destructive">*</span>
                </label>
                {validationErrors.license_plate && (
                  <div className="text-destructive text-sm mb-1">
                    {validationErrors.license_plate}
                  </div>
                )}
                <input
                  type="text"
                  name="license_plate"
                  value={form.license_plate}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-input rounded-md bg-background"
                  placeholder="e.g., ABC123GP"
                  required
                />
                <p className="text-xs text-muted-foreground mt-1">
                  South African license plate format
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Fuel Type <span className="text-destructive">*</span>
                </label>{' '}
                <CustomDropdown
                  value={form.fuel_type}
                  onChange={value => handleChange({ target: { name: 'fuel_type', value } })}
                  options={[
                    { value: 'petrol', label: 'Petrol' },
                    { value: 'diesel', label: 'Diesel' },
                    { value: 'hybrid', label: 'Hybrid' },
                    { value: 'electric', label: 'Electric' },
                  ]}
                  placeholder="Select Fuel Type"
                  maxVisibleOptions={5}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Current Mileage (km) <span className="text-destructive">*</span>
                </label>
                <input
                  type="number"
                  name="mileage"
                  value={form.mileage}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-input rounded-md bg-background"
                  min="0"
                  required
                />
              </div>
            </div>
          </div>

          {/* Status Information */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <CreditCard size={20} />
              Status Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Status <span className="text-destructive">*</span>
                </label>{' '}
                <CustomDropdown
                  value={form.status}
                  onChange={value => handleChange({ target: { name: 'status', value } })}
                  options={[
                    { value: 'active', label: 'Active' },
                    { value: 'maintenance', label: 'Maintenance' },
                    { value: 'inactive', label: 'Inactive' },
                  ]}
                  placeholder="Select Status"
                  maxVisibleOptions={5}
                />
              </div>
            </div>
          </div>

          {/* Submit Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <button
              type="button"
              onClick={closeModal}
              className="px-4 py-2 border border-border rounded-md hover:bg-accent/10 transition"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition flex items-center gap-2"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                  Updating...
                </>
              ) : (
                'Update Vehicle'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditVehicleModal;
