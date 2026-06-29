import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.ticker import PercentFormatter
from PIL import Image
import os

def create_qb_plot(data_path, columns_path, x_axis, y_axis, min_plays=100, title=None):
    # --- 1. Load and Clean Data ---
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

    # --- 2. Seaborn Styling ---
    # Setting the theme: whitegrid provides a clean background, 
    # and we'll customize the colors for a modern feel.
    sns.set_theme(style="whitegrid", font="sans-serif")
    
    fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
    fig.set_facecolor('#f8f9fa')  # Soft off-white background
    ax.set_facecolor('#f8f9fa')

    # --- 3. Helper for High-Res Logos ---
    def getImage(path, zoom_size=40):
        if not os.path.exists(path): return None
        img = Image.open(path).convert("RGBA")
        w, h = img.size
        aspect = h / w
        img = img.resize((zoom_size, int(zoom_size * aspect)), Image.Resampling.LANCZOS)
        return OffsetImage(img, zoom=1.0)

    # --- 4. Plotting ---
    mean_x = df_plot[x_axis].mean()
    mean_y = df_plot[y_axis].mean()

    # Create the "Canvas" with Seaborn (invisible points just to set the scale)
    sns.scatterplot(data=df_plot, x=x_axis, y=y_axis, alpha=0, ax=ax)

    for i, row in df_plot.iterrows():
        x, y = row[x_axis], row[y_axis]
        logo_path = f'data/logos/{row["Player Name"]}.png'
        
        # Add Logo
        img_obj = getImage(logo_path, zoom_size=38)
        if img_obj:
            ab = AnnotationBbox(img_obj, (x, y), frameon=False, zorder=3)
            ax.add_artist(ab)
        
        # Add Label (Last Name only)
        plt.annotate(row['Player Name'].split()[-1], (x, y),
                     xytext=(0, -22), textcoords='offset points', 
                     fontsize=10, fontweight='bold', color='#212529',
                     ha='center')

    # --- 5. Clean Formatting ---
    # Remove the top and right spines
    sns.despine(left=True, bottom=True)

    # Customize the grid to be very subtle
    ax.grid(True, linestyle='-', alpha=0.4, color='#ced4da', zorder=0)

    # Mean lines for quadrant separation
    ax.axvline(mean_x, color='#adb5bd', linestyle='--', lw=1.5, alpha=0.6, zorder=1)
    ax.axhline(mean_y, color='#adb5bd', linestyle='--', lw=1.5, alpha=0.6, zorder=1)

    # Titles and Labels
    ax.set_xlabel(x_axis, fontsize=12, fontweight='bold', labelpad=15, color='#495057')
    ax.set_ylabel(y_axis, fontsize=12, fontweight='bold', labelpad=15, color='#495057')
    
    # Left-aligned bold Title
    plt.title(title if title else f"{x_axis} vs {y_axis}", 
              fontsize=22, fontweight='black', loc='left', pad=25, color='#212529')

    # Axis Percent Formatting
    if y_axis in percent_cols: ax.yaxis.set_major_formatter(PercentFormatter(1))
    if x_axis in percent_cols: ax.xaxis.set_major_formatter(PercentFormatter(1))
    
    # Adding a bit of padding to the limits
    margin_x = df_plot[x_axis].std() * 0.5
    margin_y = df_plot[y_axis].std() * 0.5
    ax.set_xlim(df_plot[x_axis].min() - margin_x, df_plot[x_axis].max() + margin_x)
    ax.set_ylim(df_plot[y_axis].min() - margin_y, df_plot[y_axis].max() + margin_y)

    plt.tight_layout()
    plt.show()

# Example Call:
# create_qb_plot('chart_data.json', 'qb-columns.txt', 'EPA/Play', 'Success %', title="NFL QB Efficiency")