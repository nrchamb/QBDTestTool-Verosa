"""
UI utility functions for QuickBooks Desktop Test Tool.

Common UI helpers used across multiple tabs.
"""

import tkinter as tk
from tkinter import ttk


def create_scrollable_frame(parent):
    """
    Create a scrollable frame with canvas and scrollbar.

    Args:
        parent: Parent widget

    Returns:
        Tuple of (canvas, scrollbar, scrollable_frame)
    """
    # Create canvas and scrollbar
    canvas = tk.Canvas(parent, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    # Configure scrolling
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Mousewheel binding for smooth scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # Bind mousewheel only when mouse is over this canvas
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    return canvas, scrollbar, scrollable_frame
