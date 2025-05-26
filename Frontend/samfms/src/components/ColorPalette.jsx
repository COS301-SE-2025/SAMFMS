import React from 'react';

const ColorPalette = () => {
  // Define our primary color palette
  const primaryColors = [
    { name: '50', code: '#daeaf7' },
    { name: '100', code: '#c5e0f5' },
    { name: '200', code: '#a1cded' },
    { name: '300', code: '#7db9e5' },
    { name: '400', code: '#4fa5d8' },
    { name: '500', code: '#2A91CD' },
    { name: '600', code: '#1178b9' },
    { name: '700', code: '#0855b1' },
    { name: '800', code: '#010e54' },
    { name: '900', code: '#00022b' },
  ];

  // Semantic colors
  const semanticColors = [
    { name: 'Background', class: 'bg-background text-foreground' },
    { name: 'Foreground', class: 'bg-foreground text-background' },
    { name: 'Card', class: 'bg-card text-card-foreground' },
    { name: 'Primary', class: 'bg-primary text-primary-foreground' },
    { name: 'Secondary', class: 'bg-secondary text-secondary-foreground' },
    { name: 'Muted', class: 'bg-muted text-muted-foreground' },
    { name: 'Accent', class: 'bg-accent text-accent-foreground' },
    { name: 'Destructive', class: 'bg-destructive text-destructive-foreground' },
  ];

  return (
    <div className="container mx-auto py-8">
      <h2 className="text-2xl font-bold mb-6">Color Palette</h2>

      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-3">Primary Colors</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {primaryColors.map(color => (
            <div key={color.name} className="flex flex-col">
              <div className="h-20 rounded-md mb-2" style={{ backgroundColor: color.code }} />
              <div className="flex justify-between text-sm">
                <span className="font-medium">Primary-{color.name}</span>
                <span className="text-muted-foreground">{color.code}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3">Semantic Colors</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {semanticColors.map(color => (
            <div
              key={color.name}
              className={`${color.class} h-20 rounded-md flex items-center justify-center`}
            >
              <span className="font-medium">{color.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ColorPalette;
