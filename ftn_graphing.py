import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import os
from PIL import Image

def create_nfl_scatter_plot(csv_file, x_col, y_col, secondary_csv=None, join_key=None, 
                            title=None, label_col='Tm', x_label=None, y_label=None,
                            invert_x=False, invert_y=False):
    """
    Reads one or two NFL stats CSVs and creates a joined scatter plot with invertible axes.
    """
    
    # 1. Load and Join Data
    df = pd.read_csv(csv_file, header=1)
    
    if secondary_csv and join_key:
        df_secondary = pd.read_csv(secondary_csv, header=1)
        # Left join to maintain primary file's team list
        df = pd.merge(df, df_secondary, on=join_key, how='left', suffixes=('', '_secondary'))
    
    # 2. Clean / Preprocess Data
    # Automatically convert percentage columns if they look like 0-100 scale (mean > 1)
    for col in [x_col, y_col]:
        if col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]) and df[col].mean() > 1:
                df[col] = df[col] / 100

    # Determine Display Labels
    final_x_label = x_label if x_label else x_col
    final_y_label = y_label if y_label else y_col
    if not title:
        title = f"{final_x_label} vs {final_y_label}"

    # 3. Styling Constants
    BG_COLOR = "#f8f9fa"
    GRID_COLOR = "#e1e4e8"
    AXIS_COLOR = "#444444"
    MEAN_LINE_COLOR = "#666666"

    # 4. Create Figure
    fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # Helper for Logos
    def getImage(path, zoom_size=40):
        if not os.path.exists(path): return None
        try:
            img = Image.open(path).convert("RGBA")
            w, h = img.size
            aspect = h / w
            img = img.resize((zoom_size, int(zoom_size * aspect)), Image.Resampling.LANCZOS)
            return OffsetImage(img, zoom=1.0)
        except Exception:
            return None

    # 5. Plotting
    plot_df = df.dropna(subset=[x_col, y_col])
    
    mean_x = plot_df[x_col].mean()
    mean_y = plot_df[y_col].mean()

    for i, row in plot_df.iterrows():
        x, y = row[x_col], row[y_col]
        
        # Get Label Text
        label_text = str(row[label_col]) if label_col in plot_df.columns else ""
        
        # Logo pathing
        logo_key = row['Tm'] if 'Tm' in plot_df.columns else label_text
        logo_path = f'data/logos/{logo_key}.png'
        
        img_obj = getImage(logo_path, zoom_size=55)
        if img_obj:
            ab = AnnotationBbox(img_obj, (x, y), frameon=False, zorder=3)
            ax.add_artist(ab)
        else:
            ax.scatter(x, y, color='#3498db', alpha=0.6, s=100)

        # Updated Labeling Logic: 
        # Only remove the first word if there is more than one word (e.g., "Dallas Cowboys" -> "Cowboys")
        # Keeps abbreviations like "DAL" intact.
        label_parts = label_text.split(" ")
        clean_label = " ".join(label_parts[1:]) if len(label_parts) > 1 else label_text
        
        plt.annotate(clean_label, (x, y),
                     xytext=(0, -22), textcoords='offset points', 
                     fontsize=10, fontweight='bold', color='#111111',
                     ha='center', alpha=0.9)

    # 6. Formatting
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(AXIS_COLOR)
    ax.spines['bottom'].set_color(AXIS_COLOR)
    ax.grid(True, linestyle='-', alpha=0.5, color=GRID_COLOR, zorder=0)

    # Mean lines
    ax.axvline(mean_x, color=MEAN_LINE_COLOR, linestyle='--', lw=1.2, alpha=0.4, zorder=1)
    ax.axhline(mean_y, color=MEAN_LINE_COLOR, linestyle='--', lw=1.2, alpha=0.4, zorder=1)

    # Axis Labels and Title
    ax.set_xlabel(final_x_label, fontsize=20, fontweight='bold', color=AXIS_COLOR, labelpad=12)
    ax.set_ylabel(final_y_label, fontsize=20, fontweight='bold', color=AXIS_COLOR, labelpad=12)
    plt.title(title, fontsize=20, fontweight='black', loc='left', pad=35)
    # ax.text(0, 1.025, 'NFL Data Analysis | Reusable Grapher', transform=ax.transAxes, 
    #         fontsize=11, color='#777777', ha='left')

    # Percentage Formatting
    if plot_df[x_col].max() <= 1:
        ax.xaxis.set_major_formatter(PercentFormatter(1))
    if plot_df[y_col].max() <= 1:
        ax.yaxis.set_major_formatter(PercentFormatter(1))
    
    # --- CRITICAL FIX: Set limits first, then invert ---
    margin_x = plot_df[x_col].std() * 0.5
    margin_y = plot_df[y_col].std() * 0.5
    
    ax.set_xlim(plot_df[x_col].min() - margin_x, plot_df[x_col].max() + margin_x)
    ax.set_ylim(plot_df[y_col].min() - margin_y, plot_df[y_col].max() + margin_y)

    if invert_x:
        ax.invert_xaxis()
    if invert_y:
        ax.invert_yaxis()

    plt.tight_layout()
    plt.show()

# Example Usage:
# create_nfl_scatter_plot(
#     'offense_tendancies.csv', 
#     'PACT%', 
#     'MOT%', 
#     invert_y=True  # High values will now be at the bottom
# )