import os
import platform

system = platform.system()

if system == "Linux" or system == "Darwin":  # Linux or macOS
    # Read /proc/meminfo on Linux
    if system == "Linux":
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        
        mem_info = {}
        for line in lines:
            parts = line.split(':')
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip().split()[0]  # Get the number part
                mem_info[key] = int(value)
        
        total_kb = mem_info.get('MemTotal', 0)
        available_kb = mem_info.get('MemAvailable', 0)
        free_kb = mem_info.get('MemFree', 0)
        
        total_gb = total_kb / (1024**2)
        available_gb = available_kb / (1024**2)
        used_gb = (total_kb - available_kb) / (1024**2)
        percent = ((total_kb - available_kb) / total_kb) * 100
        
        result = f"Memory Usage Information: Total Memory is {total_gb:.2f} gigabytes. Used Memory is {used_gb:.2f} gigabytes. Available Memory is {available_gb:.2f} gigabytes. Memory Usage Percentage is {percent:.1f} percent."
    else:  # macOS
        result = "Memory information retrieval on macOS requires additional tools. Please install psutil using pip install psutil for detailed memory information."
        
elif system == "Windows":
    # Use Windows Management Instrumentation
    result = "Memory information retrieval on Windows requires additional modules. Please install psutil using pip install psutil for detailed memory information."
else:
    result = f"Unable to determine memory usage on {system} system."

print(result)