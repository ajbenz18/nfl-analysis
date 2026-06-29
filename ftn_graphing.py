import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import os
from PIL import Image

def create_nfl_scatter_plot(csv_file, x_col, y_col, y_col_2=None, secondary_csv=None, join_key=None, 
                            title=None, label_col='Tm', x_label=None, y_label=None,
                            invert_x=False, invert_y=False, show_trendline=False, show_r2=False,
                            x_is_percentage=None, y_is_percentage=None):
    """
    Reads one or two NFL stats CSVs and creates a joined scatter plot with invertible axes, 
    an extending trendline, and an optional R^2 annotation box.
    
    Args:
        csv_file (str): Path to the primary CSV file.
        x_col (str): Column name for the X-axis data.
        y_col (str): Column name for the Y-axis data.
        y_col_2 (str): column name for the y axis to add to the y_col
        secondary_csv (str, optional): Path to a second CSV file to join.
        join_key (str, optional): The common column name to join the two files on.
        title (str, optional): Custom title for the plot.
        label_col (str, optional): Column name for text annotations (default 'Tm').
        x_label (str, optional): Custom label for X-axis. Defaults to x_col name.
        y_label (str, optional): Custom label for Y-axis. Defaults to y_col name.
        invert_x (bool, optional): If True, X-axis goes from high to low.
        invert_y (bool, optional): If True, Y-axis goes from high to low.
        show_trendline (bool, optional): If True, plots a linear best-fit line.
        show_r2 (bool, optional): If True, displays the R^2 value on the chart (requires show_trendline=True).
        x_is_percentage (bool, optional): Make the x value a percentage
        y_is_percentage (bool, optional): Make the y value a percentage

    """
    
    # 1. Load and Join Data
    df = pd.read_csv(csv_file, header=1)
    
    if secondary_csv and join_key:
        df_secondary = pd.read_csv(secondary_csv, header=1)
        # Left join to maintain primary file's team list
        df = pd.merge(df, df_secondary, on=join_key, how='left', suffixes=('', '_secondary'))


    # do y_col addition
    if y_col_2:
        df['combined_y'] = df[y_col] + df[y_col_2]
        y_col = 'combined_y'

    
    # 2. Clean / Preprocess Data
    # # Automatically convert percentage columns if they look like 0-100 scale (mean > 1)
    # for col in [x_col, y_col]:
    #     if col in df.columns:
    if x_is_percentage:
        df[x_col] = df[x_col] / 100
        #     if col in df.columns:
    if y_is_percentage:
        df[y_col] = df[y_col] / 100

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
    TRENDLINE_COLOR = "#ff5a5f"  # Modern coral/red tone for the trendline

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

    # 5. Coordinate Boundaries & Calculations
    plot_df = df.dropna(subset=[x_col, y_col])
    
    mean_x = plot_df[x_col].mean()
    mean_y = plot_df[y_col].mean()

    # Calculate padding margins up-front so the trendline can leverage them
    margin_x = plot_df[x_col].std() * 0.5
    margin_y = plot_df[y_col].std() * 0.5
    
    x_min = plot_df[x_col].min() - margin_x
    x_max = plot_df[x_col].max() + margin_x
    y_min = plot_df[y_col].min() - margin_y
    y_max = plot_df[y_col].max() + margin_y

    # --- Trendline & R^2 Calculation ---
    if show_trendline and len(plot_df) > 1:
        # Calculate linear regression (y = mx + b) based on real data points
        slope, intercept = np.polyfit(plot_df[x_col], plot_df[y_col], 1)
        
        # Generate x values that span across the full padded limits
        x_vals = np.linspace(x_min, x_max, 100)
        y_vals = slope * x_vals + intercept
        
        # Plot trendline (zorder=2 sits cleanly behind logos)
        ax.plot(x_vals, y_vals, color=TRENDLINE_COLOR, linestyle='-', linewidth=2.5, alpha=0.8, zorder=2)
        
        # Optional R^2 Calculation and display
        if show_r2:
            y_pred = slope * plot_df[x_col] + intercept
            y_true = plot_df[y_col]
            ss_res = np.sum((y_true - y_pred) ** 2)
            ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)

            ax.text(0, 1.025, f'$R^2 = {r_squared:.3f}$', transform=ax.transAxes, 
                fontsize=14, color='#777777', ha='left')
        

    # 6. Plotting Individual Team Markers/Logos
    for i, row in plot_df.iterrows():
        x, y = row[x_col], row[y_col]
        
        # Get Label Text
        label_text = str(row[label_col]) if label_col in plot_df.columns else ""
        
        # Logo pathing
        logo_key = row['Tm'] if 'Tm' in plot_df.columns else label_text
        logo_path = f'data/logos/{logo_key}.png'
        
        # Add Logo or Fallback Dot
        img_obj = getImage(logo_path, zoom_size=38)
        if img_obj:
            ab = AnnotationBbox(img_obj, (x, y), frameon=False, zorder=3)
            ax.add_artist(ab)
        else:
            ax.scatter(x, y, color='#3498db', alpha=0.6, s=100)

        # Labeling Logic (removes first city/word if multi-word)
        label_parts = label_text.split(" ")
        clean_label = " ".join(label_parts[1:]) if len(label_parts) > 1 else label_text
        
        plt.annotate(clean_label, (x, y),
                     xytext=(0, -22), textcoords='offset points', 
                     fontsize=10, fontweight='bold', color='#111111',
                     ha='center', alpha=0.9)

    # 7. Formatting & Final Layout
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(AXIS_COLOR)
    ax.spines['bottom'].set_color(AXIS_COLOR)
    ax.grid(True, linestyle='-', alpha=0.5, color=GRID_COLOR, zorder=0)

    # Mean lines
    ax.axvline(mean_x, color=MEAN_LINE_COLOR, linestyle='--', lw=1.2, alpha=0.4, zorder=1)
    ax.axhline(mean_y, color=MEAN_LINE_COLOR, linestyle='--', lw=1.2, alpha=0.4, zorder=1)

    # Axis Labels and Title
    ax.set_xlabel(final_x_label, fontsize=12, fontweight='bold', color=AXIS_COLOR, labelpad=12)
    ax.set_ylabel(final_y_label, fontsize=12, fontweight='bold', color=AXIS_COLOR, labelpad=12)
    plt.title(title, fontsize=20, fontweight='black', loc='left', pad=35)


    # Percentage Formatting
    if plot_df[x_col].max() <= 1 and x_is_percentage:
        ax.xaxis.set_major_formatter(PercentFormatter(1))
    if plot_df[y_col].max() <= 1 and y_is_percentage:
        ax.yaxis.set_major_formatter(PercentFormatter(1))
    
    # Enforce padded limits
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    # Apply Inversion (Happens safely after limits are finalized)
    if invert_x:
        ax.invert_xaxis()
    if invert_y:
        ax.invert_yaxis()

    plt.tight_layout()
    plt.show()

# --- Example Usage ---
# create_nfl_scatter_plot(
#     csv_file='offense_tendancies.csv', 
#     x_col='PACT%', 
#     y_col='MOT%', 
#     show_trendline=True, 
#     show_r2=True,  # Activates the R^2 text box
#     x_label='Play Action Rate',
#     y_label='Motion Rate'
# )