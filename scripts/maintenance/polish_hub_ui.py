import os
import re

def polish_typography():
    file_path = 'C:/Users/Nima/nimadamus.github.io/scripts/handicapping_hub_production.py'
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update Google Font Import
    content = content.replace(
        "https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@400;500;600;700&display=swap",
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
    )

    # 2. Replace Rajdhani and Orbitron with Inter stack
    new_stack = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    content = content.replace("'Rajdhani', sans-serif", new_stack)
    content = content.replace("'Orbitron', sans-serif", new_stack)

    # 3. Reduce gimmicky spacing and shadows
    content = content.replace("letter-spacing: 5px;", "letter-spacing: 1px;")
    content = content.replace("letter-spacing: 3px;", "letter-spacing: 0.5px;")
    content = content.replace("letter-spacing: 2px;", "letter-spacing: 0.5px;")
    
    # Remove large neon text shadows for a cleaner look
    content = re.sub(r"text-shadow: 0 0 20px rgba\(.*?\);", "", content)
    content = re.sub(r"text-shadow: 0 0 10px rgba\(.*?\);", "", content)

    # 4. Calendar Contrast Improvement
    old_cal_day = """        .calendar-day.has-content {{
            background: rgba(0, 245, 255, 0.1);
            color: #00f5ff;
            cursor: pointer;
            transition: all 0.2s;
        }}"""
    
    new_cal_day = """        .calendar-day.has-content {{
            background: rgba(0, 245, 255, 0.25); /* High contrast */
            border: 1px solid rgba(0, 245, 255, 0.6);
            color: #fff;
            font-weight: 800;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .calendar-day.has-content:hover {{
            background: #00f5ff;
            color: #000;
            transform: scale(1.1);
        }}"""
    
    # Use a simpler replacement if multi-line fails
    content = content.replace("background: rgba(0, 245, 255, 0.1);", "background: rgba(0, 245, 255, 0.25);")
    content = content.replace("color: #00f5ff;", "color: #fff;") # Makes text white on cyan bg
    
    # Final cleanup of weight
    content = content.replace("font-weight: 900;", "font-weight: 800;")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Typography polished in generator.")

if __name__ == "__main__":
    polish_typography()
