from pynetdesign.modelling.utils import *
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import make_axes_locatable
import pandas as pd
import numpy as np
from typing import Union, Optional
import cmcrameri.cm as cmc
import warnings

def plot_sensitivity_slice(sens_data: np.ndarray, 
                           xi: np.ndarray=None, 
                           yi: np.ndarray=None,
                           zi: np.ndarray=None,
                           geometry_df: pd.DataFrame=None,
                           plot_title: str=None,
                           clb_title: str=None,
                           clb_range: tuple=None,
                           dcolormap: Optional[Union[str, mcolors.Colormap]] = 'cmc.bilbao',
                           plt_style: str='contourf',
                           plt_levels: int=None,
                           plt_contours: bool=True,
                           plot_names: bool=True,
                           station_marker_size: int = 100,
                           use_warnings: bool=True):
    r"""
    Plots magnitude sensitivity in map or side view with stations plotted as non-filled triangles with name labels.
    
    Parameters
    ----------
    sens_data : :obj:`numpy.ndarray`
        Data for sensitivity map
    xi : :obj:`numpy.ndarray`, optional
        Vector of x coordinates for sensitivity
    yi : :obj:`numpy.ndarray`, optional
        Vector of y coordinates for sensitivity
    zi : :obj:`numpy.ndarray`, optional
        Vector of z coordinates for sensitivity        
    geometry_df : :obj:`pandas.dataframe`, optional
        Geometry data frame containing station names and coordinates
    plot_title : :obj:`str`, optional
        Plot title (default: 'Magnitude sensitivity slice')
    clb_title : :obj:`str`, optional
        Colorbar title (default: '$M_w$')
    clb_range : :obj:`tuple`, optional
        Colorbar range (default: automatic)
    dcolormap : :obj:`str` or :obj:`matplotlib.colors.Colormap`, default: 'cmc.batlow'
        Data colormap to use for the plot
    plt_style : :obj:`str`, {'contourf','imshow'}, optional, default: 'contourf'
        Plot style
    plt_levels : :obj:`int`, optional, default: 21 if None
        Number of levels to plot in contours within the colorbar range.
        Has no effect on imshow
    plt_contours : :obj:`bool`, optional, default: True
        Flag to plot contours
    plot_names : :obj:`bool`, optional, default: True
        Flag to plot station names or not (True or False)
    station_marker_size : :obj:`int`, optional, default: 100
        Size of the station markers in the scatter plot
    use_warnings: :obj:`bool`, optional, default: True
        If True, enable warnings, if False, disable them

    Returns
    -------
    fig : :obj:`matplotlib.figure.Figure`
        The figure object containing the plot.
    ax : :obj:`matplotlib.axes.Axes`
        The axes object of the plot.
    cax : :obj:`matplotlib.axes.Axes`
        The axes object for the colorbar.
    cbar : :obj:`matplotlib.colorbar.Colorbar`
        The colorbar object.

    Raises
    ------
    ValueError :
        if two or more coordinate vectors are None
    ValueError :
        if all three coordinate vectors are not None
    ValueError :
        if clb_range is not a tuple with two numeric values
    ValueError :
        if plt_style is not from the list of possible types
    
    """
    # Check the input:
    if not sum(v is not None for v in [xi, yi, zi]):
        raise ValueError("Two and only two coordinate vectors must be present")
    
    # Check if plot title is set
    if plot_title is None:
        plot_title = 'Magnitude sensitivity slice'

    # Check if colorbar title is set
    if clb_title is None:
        clb_title = '$M_w$'

    # Define colormap
    if isinstance(dcolormap, str):
        cmap = plt.get_cmap(dcolormap)
    elif isinstance(dcolormap, mcolors.Colormap):
        cmap = dcolormap
    else:
        raise ValueError(f"Colormap type is unknown: {dcolormap}")

    # Check plot
    if plt_style not in ('contourf','imshow'):
        raise ValueError("Unknown plot style: " + plt_style)

    # Check plot levels
    if plt_levels is None:
        plt_levels = 21

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 10))

    # Ensure equal scaling
    ax.set_aspect('equal', 'box')

    # Add grid and labels
    ax.grid(True)    
    ax.set_title(plot_title)

    # Get plot coordinates and set axes labels
    if zi is None:
        ci1 = xi
        ci2 = yi        
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
    elif xi is None:
        ci1 = yi
        ci2 = zi        
        ax.set_xlabel('Y Coordinate')
        ax.set_ylabel('Z Coordinate')
    elif yi is None:
        ci1 = xi
        ci2 = zi        
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Z Coordinate')

    # Set extent
    extent = (ci1.min(), ci1.max(), ci2.min(), ci2.max())

    # Check data dimensions and reshape if needed
    if sens_data.ndim==1:
        sens_data = reshape_data(sens_data,ci1,ci2)
    elif sens_data.shape != (len(ci1), len(ci2)):
        plt.close(fig)
        raise ValueError("sens_data dimensions do not match coordinate vectors.")
    
    # Transpose data for plotting
    pdata = np.transpose(sens_data)

    # Check and set colorbar range
    if clb_range is not None:
        # Check if clb_range is a tuple with two values
        if (not isinstance(clb_range, tuple) or 
                len(clb_range) != 2 or 
                not contains_only_numeric(clb_range)):
            raise ValueError("clb_range must be a tuple with two numeric values")
        else:            
            ax.set_clim = clb_range
            levels = np.linspace(clb_range[0],clb_range[1],plt_levels)
    else:
        levels = plt_levels
           
    # Plot the sensitivity data as a heatmap in desired style    
    if plt_style == "contourf":
        im = ax.contourf(ci1,ci2,pdata, levels, cmap=cmap, extent=extent)
    elif plt_style == "imshow":
        im = ax.imshow(pdata,
                       origin='lower',
                       extent=extent,
                       cmap=cmap)
    else:
        raise ValueError("Unknown plot style: " + plt_style)

    # Plot contours
    if plt_contours:   
        ax.contour(ci1,ci2,pdata, levels, colors='k', origin='lower', extent=extent, linewidths=0.5)

    # Set axis limits
    ax.set_xlim(ci1.min(), ci1.max())
    if zi is None:        
        ax.set_ylim(ci2.min(), ci2.max())
    else: #reversed for side views
        ax.set_ylim(ci2.max(), ci2.min())
        
    # Enable axis divider
    divider = make_axes_locatable(ax)
    # Create an axes on the right side of ax. The width of cax will be 5%
    # of ax and the padding between cax and ax will be fixed at 0.2 inch.
    cax = divider.append_axes("right", size="5%", pad=0.2)
    # Create colorbar on the new axes
    cbar = plt.colorbar(im, cax=cax, location='right')

    # Colorbar title
    cbar.set_label(clb_title)  

    # Plot stations
    if geometry_df is not None:
        
        # Extract data from the data frame
        if zi is None:        
            cs1 = geometry_df['X']
            cs2 = geometry_df['Y']
        elif yi is None:
            cs1 = geometry_df['X']
            cs2 = geometry_df['Z']            
        elif xi is None:
            cs1 = geometry_df['Y']
            cs2 = geometry_df['Z']                
        
        # Check if Name column can be used
        if plot_names:
            if 'Name' in geometry_df.columns:
                names = geometry_df['Name']
            else:
                plot_names = False
                if use_warnings:
                    warnings.warn("Can't plot station names: Name column is missing in the geometry data.")
        
        # Create a scatter plot with triangles        
        scatter = ax.scatter(cs1, cs2, s=station_marker_size, marker='^', facecolors='none', edgecolors='black')
   
        # Add labels to the points with vertical alignment to bottom
        if plot_names:
            for i, name in enumerate(names):
                if isinstance(name, str):
                    name = name + " " # to make a gap between the name and the marker
                    ax.text(cs1[i], cs2[i], name, fontsize=12, ha='right', va='bottom')
    
    plt.show()

    return fig, ax, cax, cbar