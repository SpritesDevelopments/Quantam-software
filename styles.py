from tkinter import ttk, messagebox

LIGHT_THEME = {
    'bg': '#ffffff',            # White background
    'fg': '#000000',            # Black text
    'button_bg': '#f0f0f0',     # Light gray button
    'button_fg': '#000000',     # Black button text
    'entry_bg': '#ffffff',      # White entry background
    'entry_fg': '#000000',      # Black entry text
    'text_bg': '#ffffff',       # White text background
    'text_fg': '#000000',       # Black text
    'select_bg': '#0078d7',     # Windows blue selection
    'accent': '#0078d7',        # Windows blue accent
    'error': '#cc0000',         # Dark red
    'success': '#008000',       # Dark green
    'active': '#e5f3ff',        # Light blue for active
    'border': '#cccccc'         # Light gray border
}

def apply_light_theme(root):
    style = ttk.Style(root)
    
    # Configure base theme settings
    style.configure('.',
        background=LIGHT_THEME['bg'],
        foreground=LIGHT_THEME['fg'],
        fieldbackground=LIGHT_THEME['entry_bg']
    )
    
    # Custom button style
    style.configure('Custom.TButton',
        font=('Segoe UI', 10),
        padding=(10, 5)
    )
    style.map('Custom.TButton',
        background=[('active', LIGHT_THEME['active']), ('!active', LIGHT_THEME['button_bg'])],
        foreground=[('active', LIGHT_THEME['fg']), ('!active', LIGHT_THEME['button_fg'])]
    )
    
    # Frame styling
    style.configure('Custom.TFrame',
        background=LIGHT_THEME['bg']
    )
    
    # Notebook styling
    style.configure('Custom.TNotebook',
        background=LIGHT_THEME['bg']
    )
    style.configure('Custom.TNotebook.Tab',
        font=('Segoe UI', 10),
        padding=[15, 5]
    )
    style.map('Custom.TNotebook.Tab',
        background=[('selected', LIGHT_THEME['accent'])],
        foreground=[('selected', '#ffffff')]
    )
    
    # Entry styling
    style.configure('Custom.TEntry',
        fieldbackground=LIGHT_THEME['entry_bg'],
        foreground=LIGHT_THEME['entry_fg']
    )

    # Label styling
    style.configure('Custom.TLabel',
        background=LIGHT_THEME['bg'],
        foreground=LIGHT_THEME['fg'],
        font=('Segoe UI', 10)
    )

    # Add toolbar button style
    style.configure('Toolbar.TButton',
        padding=4,
        relief='flat',
        background=LIGHT_THEME['bg'],
        foreground=LIGHT_THEME['fg']
    )
    style.map('Toolbar.TButton',
        background=[('active', LIGHT_THEME['active'])],
        foreground=[('active', LIGHT_THEME['fg'])]
    )

    # Activity bar button style
    style.configure('Activity.TButton',
        padding=5,
        relief='flat',
        background=LIGHT_THEME['bg'],
        foreground=LIGHT_THEME['fg']
    )
    
    style.configure('Activity.TButton.Hover',
        background=LIGHT_THEME['active'],
        foreground=LIGHT_THEME['fg']
    )

    return LIGHT_THEME

def apply_dark_theme(root):
    messagebox.showinfo("Coming Soon", "Dark mode is coming soon!")
    return LIGHT_THEME
