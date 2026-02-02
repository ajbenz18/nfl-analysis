import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.ticker import PercentFormatter
from PIL import Image
import os

def create_qb_plot(data_path, columns_path, x_axis, y_axis, min_plays=100, title=None):
    # 1. Load and Clean Data
    with open(columns_path, 'r') as f:
        columns = [line.strip() for line in f if line.strip() and not line.startswith('[source')]

    with open(data_path, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data, columns=columns)
    df['Player Name'] = df['Player Name'].str.split('. ', n=1).str[-1]

    percent_cols = ['Scramble %', 'Sack %', 'Success %', 'Comp %']
    for col in df.columns:
        if col in ['Player Name', 'Season', 'Team']: continue
        if col in percent_cols:
            df[col] = df[col].astype(str).str.rstrip('%').replace('', np.nan).astype(float) / 100.0
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df_plot = df[df['Plays'] >= min_plays].copy()

    # 2. Styling Constants
    BG_COLOR = "#f8f9fa"  # Modern soft grey-white
    GRID_COLOR = "#e1e4e8"
    AXIS_COLOR = "#444444"
    MEAN_LINE_COLOR = "#666666"

    # 3. Create Figure
    fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # 4. Helper for Logos (High-Res PIL Resize)
    def getImage(path, zoom_size=40):
        if not os.path.exists(path): return None
        img = Image.open(path).convert("RGBA")
        w, h = img.size
        aspect = h / w
        img = img.resize((zoom_size, int(zoom_size * aspect)), Image.Resampling.LANCZOS)
        return OffsetImage(img, zoom=1.0)

    # 5. Plotting
    mean_x = df_plot[x_axis].mean()
    mean_y = df_plot[y_axis].mean()

    for i, row in df_plot.iterrows():
        x, y = row[x_axis], row[y_axis]
        logo_path = f'data/logos/{row["Player Name"]}.png'
        
        # Add Logo
        img_obj = getImage(logo_path, zoom_size=38)
        if img_obj:
            ab = AnnotationBbox(img_obj, (x, y), frameon=False, zorder=3)
            ax.add_artist(ab)
        
        # Add Label (Last Name only for cleanliness)
        plt.annotate(row['Player Name'].split()[-1], (x, y),
                     xytext=(0, -20), textcoords='offset points', 
                     fontsize=9, fontweight='bold', color='#111111',
                     ha='center', alpha=0.9)

    # 6. Modern Formatting
    # Remove top and right borders (Spines)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(AXIS_COLOR)
    ax.spines['bottom'].set_color(AXIS_COLOR)

    # Add a clean, visible grid behind logos
    ax.grid(True, linestyle='-', alpha=0.5, color=GRID_COLOR, zorder=0)

    # Thick mean lines to create quadrants
    ax.axvline(mean_x, color=MEAN_LINE_COLOR, linestyle='--', lw=1.2, alpha=0.4, zorder=1)
    ax.axhline(mean_y, color=MEAN_LINE_COLOR, linestyle='--', lw=1.2, alpha=0.4, zorder=1)

    # Labels and Titles
    ax.set_xlabel(x_axis, fontsize=12, fontweight='bold', color=AXIS_COLOR, labelpad=12)
    ax.set_ylabel(y_axis, fontsize=12, fontweight='bold', color=AXIS_COLOR, labelpad=12)
    
    # Left-aligned bold title + subtitle
    plt.title(title if title else f"{x_axis} vs {y_axis}", 
              fontsize=20, fontweight='black', loc='left', pad=35)
    ax.text(0, 1.025, '2025 Regular Season | Minimum 100 Plays', transform=ax.transAxes, 
            fontsize=11, color='#777777', ha='left')

    # Axis Formatting
    if y_axis in percent_cols: ax.yaxis.set_major_formatter(PercentFormatter(1))
    if x_axis in percent_cols: ax.xaxis.set_major_formatter(PercentFormatter(1))
    
    # Set generous limits so logos aren't cut off
    margin_x = df_plot[x_axis].std() * 0.4
    margin_y = df_plot[y_axis].std() * 0.4
    ax.set_xlim(df_plot[x_axis].min() - margin_x, df_plot[x_axis].max() + margin_x)
    ax.set_ylim(df_plot[y_axis].min() - margin_y, df_plot[y_axis].max() + margin_y)

    plt.tight_layout()
    plt.show()

# create_qb_plot('chart_data.json', 'qb-columns.txt', 'EPA/Play', 'Success %')