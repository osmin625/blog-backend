import os
import re
import shutil
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def get_prefixed_name(file_path: Path, src_dir: Path) -> str:
    """
    Generates a prefixed filename based on the directory structure relative to src_dir.
    e.g., source/folder/subfolder/file.md -> folder - subfolder - file.md
    """
    relative_path = file_path.relative_to(src_dir)
    parts = list(relative_path.parts)
    
    if len(parts) == 1:
        return parts[0]
        
    # Join directory parts with ' - ' and append the filename
    prefix = " - ".join(parts[:-1])
    return f"{prefix} - {parts[-1]}"

def process_links(content: str, filename_map: dict) -> str:
    """
    Updates Obsidian wikilinks in the content using the filename mapping.
    """
    def link_replacer(match):
        inner = match.group(1)
        if '|' in inner:
            page, alias = inner.split('|', 1)
        else:
            page, alias = inner, inner
        
        # Look for the page in our map (ignoring case for safety, though Obsidian is case sensitive usually)
        page_md = f"{page}.md".lower()
        new_page_name = None
        
        for old_name, new_name in filename_map.items():
            if old_name.lower() == page_md:
                new_page_name = new_name[:-3] # Remove .md extension for wikilink
                break
                
        if new_page_name:
            if alias != page: # if aliased
                 return f"[[{new_page_name}|{alias}]]"
            else:
                 return f"[[{new_page_name}]]"
                 
        # If not found, return original
        return match.group(0)

    # Match [[link]] or [[link|alias]]
    return re.sub(r'\[\[(.*?)\]\]', link_replacer, content)

def main():
    parser = argparse.ArgumentParser(description="Normalize nested Obsidian directory to a flat structure with prefixes.")
    parser.add_argument("--src-dir", required=True, help="Source directory containing nested markdown files")
    parser.add_argument("--dest-dir", required=True, help="Destination directory for flat structure")
    args = parser.parse_args()

    src_dir = Path(args.src_dir)
    dest_dir = Path(args.dest_dir)

    if not src_dir.exists():
         logging.error(f"Source directory '{src_dir}' does not exist.")
         return

    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Pass 1: Map old filenames to new prefixed filenames
    filename_map = {} # {old_filename: new_prefixed_filename}
    file_paths = []
    
    for filepath in src_dir.rglob('*.md'):
        if filepath.is_file():
            new_name = get_prefixed_name(filepath, src_dir)
            
            # Warn if there's a collision (multiple files with same name in same folder unlikely, but different folders could theoretically clash if one had '-' in name)
            if filepath.name in filename_map:
                 logging.warning(f"Duplicate filename detected before prefixing: {filepath.name}")
            
            filename_map[filepath.name] = new_name
            file_paths.append(filepath)

    logging.info(f"Mapped {len(file_paths)} markdown files.")

    # Pass 2: Process files, update links, and copy to destination
    for filepath in file_paths:
        try:
            content = filepath.read_text(encoding='utf-8')
            new_content = process_links(content, filename_map)
            
            new_name = filename_map[filepath.name]
            dest_path = dest_dir / new_name
            
            dest_path.write_text(new_content, encoding='utf-8')
            logging.info(f"Processed: {filepath.relative_to(src_dir)} -> {new_name}")
            
        except Exception as e:
             logging.error(f"Error processing {filepath}: {e}")
             
    # Pass 3: Copy non-markdown files (images, etc) directly if they don't have collisions
    # This keeps assets intact, but they won't be prefixed.
    for filepath in src_dir.rglob('*'):
         if filepath.is_file() and filepath.suffix != '.md':
              # For assets, we might want to just dump them in a 'images' subfolder or flat
              # Here we'll just put them flat in dest_dir for simplicity, or we can keep them in 'images'
              # if they are in an images folder.
               dest_path = dest_dir / filepath.name
               
               if dest_path.exists():
                   logging.warning(f"Asset collision: {filepath.name} already exists. Overwriting.")
                   
               shutil.copy2(filepath, dest_path)
               logging.info(f"Copied asset: {filepath.name}")
               
    logging.info("Normalization complete.")

if __name__ == "__main__":
    main()
