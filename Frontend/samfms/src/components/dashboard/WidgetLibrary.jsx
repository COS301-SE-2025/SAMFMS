import React, {useState, useRef, useEffect} from 'react';
import {Plus, Search, X} from 'lucide-react';
import {getAllWidgets, WIDGET_CATEGORIES, generateWidgetId} from '../../utils/widgetRegistry';
import {useDashboard} from '../../contexts/DashboardContext';

export const WidgetLibrary = ({isOpen, onClose}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const {dispatch} = useDashboard();
  const searchInputRef = useRef(null);

  // Focus the search input when the component opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      // Use setTimeout to ensure the modal is fully rendered before focusing
      const timer = setTimeout(() => {
        searchInputRef.current.focus();
      }, 100);

      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  const allWidgets = getAllWidgets();
  const categories = Object.values(WIDGET_CATEGORIES);

  const filteredWidgets = allWidgets.filter(([type, {metadata}]) => {
    const matchesSearch =
      metadata.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      metadata.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || metadata.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleAddWidget = (type, metadata) => {
    const newWidget = {
      id: generateWidgetId(),
      type,
      config: {
        title: metadata.title,
      },
      size: metadata.defaultSize,
    };

    dispatch({type: 'ADD_WIDGET', payload: newWidget});
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Widget Library</h2>
            <button onClick={onClose} className="hover:bg-muted rounded p-1">
              <X size={20} />
            </button>
          </div>

          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                size={18}
              />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search widgets..."
                className="w-full pl-10 pr-4 py-2 border border-input rounded-md"
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
            </div>
            <select
              className="px-3 py-2 border border-input rounded-md"
              value={selectedCategory}
              onChange={e => setSelectedCategory(e.target.value)}
            >
              <option value="all">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="p-4 overflow-y-auto max-h-[60vh]">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredWidgets.map(([type, {metadata}]) => (
              <div
                key={type}
                className="border border-border rounded-lg p-4 hover:bg-accent/5 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {React.createElement(metadata.icon, {
                      size: 20,
                      className: 'text-muted-foreground',
                    })}
                    <h3 className="font-medium">{metadata.title}</h3>
                  </div>
                  <button
                    onClick={() => handleAddWidget(type, metadata)}
                    className="p-1 bg-primary text-primary-foreground rounded hover:bg-primary/90"
                    title="Add Widget"
                  >
                    <Plus size={16} />
                  </button>
                </div>
                <p className="text-sm text-muted-foreground mb-2">{metadata.description}</p>
                <span className="text-xs bg-muted px-2 py-1 rounded">{metadata.category}</span>
              </div>
            ))}
          </div>

          {filteredWidgets.length === 0 && (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No widgets found matching your criteria</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
