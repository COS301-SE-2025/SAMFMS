import React from 'react';
import { X, PlusCircle } from 'lucide-react';

const TagList = ({ tags, onRemoveTag, onAddTag }) => {
  return (
    <div className="flex flex-wrap gap-2">
      {tags.map(tag => (
        <span
          key={tag}
          className="bg-primary/10 text-primary text-xs px-2 py-1 rounded-full flex items-center"
        >
          {tag}
          {onRemoveTag && (
            <X size={12} className="ml-1 cursor-pointer" onClick={() => onRemoveTag(tag)} />
          )}
        </span>
      ))}
      {onAddTag && (
        <button
          className="text-muted-foreground hover:text-primary text-xs border border-dashed border-border px-2 py-1 rounded-full flex items-center"
          onClick={onAddTag}
        >
          <PlusCircle size={12} className="mr-1" />
          Add Tag
        </button>
      )}
    </div>
  );
};

export default TagList;
