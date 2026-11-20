"""
Analyzer - Data analysis, calculations, and report generation.
Provides simulation and analysis capabilities like movie JARVIS.
"""

import csv
import json
import math
import statistics
import logging
import io
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

import psutil

logger = logging.getLogger('JARVIS.tools.analyzer')


class Analyzer:
    """Data analysis, calculations, and report generation"""
    
    def __init__(self, config: dict):
        self.config = config.get('analyzer', {})
        self.max_file_size = self.config.get('max_file_size_mb', 10) * 1024 * 1024
        logger.info("Analyzer initialized")
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a file and return statistics and summary.
        Supports CSV, JSON, and text files.
        """
        path = Path(file_path)
        
        if not path.exists():
            return {"error": f"File not found: {file_path}"}
        
        # Check file size
        if path.stat().st_size > self.max_file_size:
            return {"error": f"File too large: {path.stat().st_size / (1024*1024):.1f}MB (max {self.config.get('max_file_size_mb', 10)}MB)"}
        
        try:
            if path.suffix.lower() == '.csv':
                return self._analyze_csv(path)
            elif path.suffix.lower() == '.json':
                return self._analyze_json(path)
            elif path.suffix.lower() in ['.txt', '.md', '.py', '.js', '.html', '.css']:
                return self._analyze_text(path)
            else:
                return {"error": f"Unsupported file type: {path.suffix}"}
        except Exception as e:
            return {"error": f"Error analyzing file: {str(e)}"}
    
    def _analyze_csv(self, path: Path) -> Dict[str, Any]:
        """Analyze a CSV file"""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        columns = reader.fieldnames or []
        
        if not rows:
            return {"type": "csv", "rows": 0, "columns": 0, "message": "Empty CSV file"}
        
        analysis = {
            "type": "csv",
            "file": str(path.name),
            "rows": len(rows),
            "columns": len(columns),
            "column_names": columns,
            "column_stats": {},
        }
        
        # Analyze each column
        for col in columns:
            values = [row[col] for row in rows if row.get(col)]
            
            # Try numeric analysis
            numeric_values = []
            for val in values:
                try:
                    numeric_values.append(float(val))
                except (ValueError, TypeError):
                    pass
            
            if numeric_values:
                analysis["column_stats"][col] = {
                    "type": "numeric",
                    "count": len(numeric_values),
                    "mean": round(statistics.mean(numeric_values), 2),
                    "median": round(statistics.median(numeric_values), 2),
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "stdev": round(statistics.stdev(numeric_values), 2) if len(numeric_values) > 1 else 0,
                }
            else:
                # Text analysis
                unique_values = set(values)
                analysis["column_stats"][col] = {
                    "type": "text",
                    "count": len(values),
                    "unique_values": len(unique_values),
                    "top_values": dict(self._most_common(values, 5)),
                }
        
        return analysis
    
    def _analyze_json(self, path: Path) -> Dict[str, Any]:
        """Analyze a JSON file"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        analysis = {
            "type": "json",
            "file": str(path.name),
        }
        
        if isinstance(data, list):
            analysis["structure"] = "array"
            analysis["items"] = len(data)
            if data:
                analysis["sample"] = data[0] if len(data) > 0 else None
                analysis["keys"] = list(data[0].keys()) if isinstance(data[0], dict) else None
        elif isinstance(data, dict):
            analysis["structure"] = "object"
            analysis["keys"] = len(data)
            analysis["top_level_keys"] = list(data.keys())[:10]
            analysis["sample"] = {k: v for k, v in list(data.items())[:3]}
        
        return analysis
    
    def _analyze_text(self, path: Path) -> Dict[str, Any]:
        """Analyze a text file"""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        words = content.split()
        characters = len(content)
        
        # Word frequency
        word_freq = self._most_common(words, 10)
        
        analysis = {
            "type": "text",
            "file": str(path.name),
            "characters": characters,
            "words": len(words),
            "lines": len(lines),
            "average_words_per_line": round(len(words) / max(len(lines), 1), 1),
            "top_words": dict(word_freq),
            "unique_words": len(set(words.lower())),
        }
        
        return analysis
    
    def _most_common(self, items: List[str], n: int = 10) -> List[tuple]:
        """Get most common items"""
        freq = {}
        for item in items:
            freq[item.lower()] = freq.get(item.lower(), 0) + 1
        return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def calculate(self, expression: str) -> Dict[str, Any]:
        """
        Perform complex calculations.
        Supports: basic math, percentages, unit conversions, financial calculations.
        """
        expression = expression.strip().lower()
        
        try:
            # Percentage calculation: "15% of 250"
            if '%' in expression and 'of' in expression:
                parts = expression.split('%')
                percent = float(parts[0].strip())
                of_parts = parts[1].split('of')
                if len(of_parts) > 1:
                    total = float(of_parts[1].strip())
                    result = (percent / 100) * total
                    return {
                        "type": "percentage",
                        "expression": f"{percent}% of {total}",
                        "result": result,
                    }
            
            # Unit conversion: "convert 100 celsius to fahrenheit"
            if 'convert' in expression or 'to' in expression:
                return self._unit_conversion(expression)
            
            # Financial: "compound interest" or "loan"
            if 'interest' in expression or 'loan' in expression or 'emi' in expression:
                return self._financial_calculation(expression)
            
            # Basic math expression
            # Only allow safe characters
            safe_expr = expression.replace('^', '**')
            if all(c in '0123456789.+-*/() ' for c in safe_expr):
                result = eval(safe_expr)
                return {
                    "type": "math",
                    "expression": expression,
                    "result": result,
                }
            
            return {"error": "Could not parse calculation. Try: '15% of 250', '2 + 2', or 'convert 100 celsius to fahrenheit'"}
        
        except Exception as e:
            return {"error": f"Calculation error: {str(e)}"}
    
    def _unit_conversion(self, expression: str) -> Dict[str, Any]:
        """Handle unit conversions"""
        # Temperature
        if 'celsius' in expression and 'fahrenheit' in expression:
            numbers = [float(x) for x in expression.split() if x.replace('.', '', 1).isdigit()]
            if numbers:
                celsius = numbers[0]
                fahrenheit = (celsius * 9/5) + 32
                return {"type": "temperature", "from": f"{celsius}°C", "to": f"{fahrenheit:.1f}°F", "result": fahrenheit}
        
        if 'fahrenheit' in expression and 'celsius' in expression:
            numbers = [float(x) for x in expression.split() if x.replace('.', '', 1).isdigit()]
            if numbers:
                fahrenheit = numbers[0]
                celsius = (fahrenheit - 32) * 5/9
                return {"type": "temperature", "from": f"{fahrenheit}°F", "to": f"{celsius:.1f}°C", "result": celsius}
        
        # Length
        if 'km' in expression and 'mile' in expression or 'miles' in expression:
            numbers = [float(x) for x in expression.split() if x.replace('.', '', 1).isdigit()]
            if numbers:
                km = numbers[0]
                miles = km * 0.621371
                return {"type": "length", "from": f"{km} km", "to": f"{miles:.2f} miles", "result": miles}
        
        if 'mile' in expression and 'km' in expression:
            numbers = [float(x) for x in expression.split() if x.replace('.', '', 1).isdigit()]
            if numbers:
                miles = numbers[0]
                km = miles * 1.60934
                return {"type": "length", "from": f"{miles} miles", "to": f"{km:.2f} km", "result": km}
        
        # Weight
        if 'kg' in expression and ('pound' in expression or 'lbs' in expression):
            numbers = [float(x) for x in expression.split() if x.replace('.', '', 1).isdigit()]
            if numbers:
                kg = numbers[0]
                lbs = kg * 2.20462
                return {"type": "weight", "from": f"{kg} kg", "to": f"{lbs:.2f} lbs", "result": lbs}
        
        return {"error": "Unsupported conversion. Try: temperature (Celsius/Fahrenheit), length (km/miles), weight (kg/lbs)"}
    
    def _financial_calculation(self, expression: str) -> Dict[str, Any]:
        """Handle financial calculations"""
        numbers = [float(x) for x in expression.split() if x.replace('.', '', 1).isdigit()]
        
        if 'emi' in expression or 'loan' in expression:
            if len(numbers) >= 3:
                principal = numbers[0]
                rate = numbers[1] / 1200  # Monthly rate
                months = numbers[2]
                emi = principal * rate * (1 + rate)**months / ((1 + rate)**months - 1)
                return {
                    "type": "emi",
                    "principal": principal,
                    "rate": numbers[1],
                    "months": months,
                    "emi": round(emi, 2),
                    "total_payment": round(emi * months, 2),
                    "total_interest": round(emi * months - principal, 2),
                }
        
        if 'interest' in expression or 'compound' in expression:
            if len(numbers) >= 3:
                principal = numbers[0]
                rate = numbers[1] / 100
                years = numbers[2]
                amount = principal * (1 + rate)**years
                return {
                    "type": "compound_interest",
                    "principal": principal,
                    "rate": numbers[1],
                    "years": years,
                    "final_amount": round(amount, 2),
                    "interest_earned": round(amount - principal, 2),
                }
        
        return {"error": "Could not parse financial calculation. Try: 'EMI 100000 12 24' or 'compound interest 10000 8 5'"}
    
    def generate_system_report(self) -> Dict[str, Any]:
        """Generate a comprehensive system status report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu": {
                    "usage_percent": psutil.cpu_percent(interval=1),
                    "cores": psutil.cpu_count(),
                    "freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                },
                "memory": {
                    "total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                    "available_gb": round(psutil.virtual_memory().available / (1024**3), 1),
                    "used_percent": psutil.virtual_memory().percent,
                },
                "disk": {
                    "total_gb": round(psutil.disk_usage('C:\\').total / (1024**3), 1),
                    "free_gb": round(psutil.disk_usage('C:\\').free / (1024**3), 1),
                    "used_percent": psutil.disk_usage('C:\\').percent,
                },
            },
        }
        
        # Battery info (if available)
        battery = psutil.sensors_battery()
        if battery:
            report["battery"] = {
                "percent": battery.percent,
                "plugged_in": battery.power_plugged,
                "secs_left": battery.secsleft,
            }
        
        # Top processes by CPU
        processes = sorted(psutil.process_iter(['cpu_percent', 'memory_percent', 'name']), 
                         key=lambda x: x.info.get('cpu_percent', 0), reverse=True)[:5]
        report["top_processes"] = [
            {
                "name": p.info.get('name', 'unknown'),
                "cpu_percent": p.info.get('cpu_percent', 0),
                "memory_percent": p.info.get('memory_percent', 0),
            }
            for p in processes
        ]
        
        return report
    
    def generate_learning_report(self, learning_stats: Dict, internet_stats: Dict, 
                                local_stats: Dict, deep_memory_stats: Dict) -> str:
        """Generate a human-readable learning progress report"""
        lines = []
        lines.append("=== JARVIS Learning Report ===")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        
        # Learning AI stats
        if learning_stats:
            lines.append("--- Self-Learning AI ---")
            lines.append(f"Memories stored: {learning_stats.get('memories', 0)}")
            lines.append(f"Patterns learned: {learning_stats.get('patterns', 0)}")
            lines.append(f"Categories: {learning_stats.get('categories', 0)}")
            lines.append("")
        
        # Internet learning stats
        if internet_stats:
            lines.append("--- Internet Learning ---")
            lines.append(f"Topics learned: {internet_stats.get('topics_learned', 0)}")
            lines.append(f"Sessions completed: {internet_stats.get('total_sessions', 0)}")
            lines.append(f"Status: {internet_stats.get('status', 'unknown')}")
            lines.append("")
        
        # Local learning stats
        if local_stats:
            lines.append("--- Local AI Brain ---")
            lines.append(f"Words learned: {local_stats.get('words_learned', 0)}")
            lines.append(f"Entities known: {local_stats.get('entities_known', 0)}")
            lines.append("")
        
        # Deep memory stats
        if deep_memory_stats:
            lines.append("--- Deep Memory ---")
            lines.append(f"Conversations stored: {deep_memory_stats.get('conversation_count', 0)}")
            lines.append(f"Preferences: {deep_memory_stats.get('preference_count', 0)}")
            lines.append(f"Topics tracked: {deep_memory_stats.get('topic_count', 0)}")
            lines.append("")
        
        return "\n".join(lines)
