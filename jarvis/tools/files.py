"""
File Assistant - Search, read, and manage files
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger('JARVIS.tools.files')


class FileAssistant:
    """Search, read, and manage files"""
    
    def __init__(self, config: dict):
        self.config = config.get('system', {})
        self.favorite_dirs = self.config.get('favorite_dirs', {})
        self.max_file_size = 10 * 1024 * 1024  # 10MB max for reading
        logger.info("FileAssistant initialized")
    
    def search_files(self, query: str, directories: List[str] = None) -> List[Dict]:
        """Search for files by name"""
        if directories is None:
            directories = list(self.favorite_dirs.values())
        
        results = []
        query_lower = query.lower()
        
        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue
            
            try:
                for root, dirs, files in os.walk(dir_path):
                    # Skip hidden and system directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                              ['node_modules', '__pycache__', '.git', '.venv', 'venv']]
                    
                    for filename in files:
                        if query_lower in filename.lower():
                            filepath = Path(root) / filename
                            try:
                                stat = filepath.stat()
                                results.append({
                                    'name': filename,
                                    'path': str(filepath),
                                    'size': self._format_size(stat.st_size),
                                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                                })
                            except (PermissionError, OSError):
                                continue
                    
                    # Limit results
                    if len(results) >= 50:
                        break
            except (PermissionError, OSError):
                continue
            
            if len(results) >= 50:
                break
        
        return results
    
    def list_files(self, directory: str = None) -> List[Dict]:
        """List files in a directory"""
        if directory is None:
            directory = self.favorite_dirs.get('documents', str(Path.home()))
        
        dir_path = Path(directory)
        if not dir_path.exists():
            # Try favorite dirs
            for name, path in self.favorite_dirs.items():
                if directory.lower() in name.lower():
                    dir_path = Path(path)
                    break
        
        if not dir_path.exists():
            return []
        
        results = []
        try:
            for item in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    stat = item.stat()
                    results.append({
                        'name': item.name,
                        'path': str(item),
                        'is_directory': item.is_dir(),
                        'size': self._format_size(stat.st_size) if not item.is_dir() else '-',
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                    })
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError) as e:
            logger.error(f"Error listing {directory}: {e}")
        
        return results
    
    def read_file(self, filepath: str) -> Optional[str]:
        """Read a file's content"""
        file_path = Path(filepath)
        if not file_path.exists():
            return None
        
        if not file_path.is_file():
            return f"{filepath} is a directory, not a file"
        
        # Check file size
        if file_path.stat().st_size > self.max_file_size:
            return f"File too large ({self._format_size(file_path.stat().st_size)}). Max: 10MB"
        
        # Check if it's a text file
        if not self._is_text_file(file_path):
            return f"File appears to be binary. Cannot display content."
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error reading file: {e}"
    
    def get_file_info(self, filepath: str) -> Optional[Dict]:
        """Get detailed file information"""
        file_path = Path(filepath)
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'path': str(file_path),
                'size': self._format_size(stat.st_size),
                'size_bytes': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'accessed': datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S'),
                'is_directory': file_path.is_dir(),
                'extension': file_path.suffix,
            }
        except Exception as e:
            return {'error': str(e)}
    
    def open_file(self, filepath: str) -> str:
        """Open a file with default application"""
        file_path = Path(filepath)
        if not file_path.exists():
            return f"File not found: {filepath}"
        
        try:
            os.startfile(str(file_path))
            return f"Opening {file_path.name}..."
        except Exception as e:
            return f"Error opening file: {e}"
    
    def _is_text_file(self, filepath: Path) -> bool:
        """Check if a file is a text file"""
        text_extensions = {
            '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs', '.go', '.rs',
            '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.toml', '.ini',
            '.md', '.txt', '.log', '.csv', '.sql', '.sh', '.bat', '.ps1',
            '.php', '.rb', '.pl', '.swift', '.kt', '.scala',
            '.cfg', '.conf', '.env', '.gitignore',
        }
        
        if filepath.suffix.lower() in text_extensions:
            return True
        
        # Try reading first bytes
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' not in chunk
        except Exception:
            return False
    
    def _format_size(self, size: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def get_favorite_dirs(self) -> Dict[str, str]:
        """Get favorite directories"""
        return dict(self.favorite_dirs)
