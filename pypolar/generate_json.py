import json
from pathlib import Path

orange = ('#FF7F4F', '#ffb295')
text_color = 'black'
red = ('#B54D42', '#d5928b')
green = ('#ADD1AD', '#cee3ce')
blue = ('#0047AB', '#0047AB')
gray = ('#7F7F7F', '#A6A6A6')

font_macosx = 'Arial Rounded MT Bold'
font_windows = 'Segoe UI'
font_linux = 'Ubuntu'

file = Path(__file__).parent / 'polarimetry.json'

if not file.exists():
  data = {
    'CTk': {
      'fg_color': gray[0]
    },
    'CTkToplevel': {
      'fg_color': gray[0]
    },
    'CTkFrame': {
      'corner_radius': 6,
      'border_width': 0,
      'fg_color': gray[0],
      'top_fg_color': gray[0],
      'border_color': gray[1]
    },
    'CTkScrollableFrame': {
      'corner_radius': 6,
      'border_width': 0,
      'fg_color': gray[1],
      'label_fg_color': text_color
    },
    'CTkButton': {
      'corner_radius': 6,
      'border_width': 0,
      'fg_color': orange[0],
      'hover_color': orange[1],
      'border_color': orange[0],
      'text_color': text_color,
      'text_color_disabled': gray[0]
    },
    'CTkLabel': {
      'corner_radius': 0,
      'fg_color': 'transparent',
      'text_color': text_color
    },
    'CTkEntry': {
      'corner_radius': 6,
      'border_width': 2,
      'fg_color': 'transparent',
      'border_color': gray[1],
      'text_color': text_color,
      'placeholder_text_color': text_color
    },
    'CTkCheckbox': {
      'corner_radius': 6,
      'border_width': 3,
      'fg_color': orange[0],
      'border_color': gray[1],
      'hover_color': orange[1],
      'checkmark_color': text_color,
      'text_color': text_color,
      'text_color_disabled': gray[1]
    },
    'CTkSwitch': {
      'corner_radius': 1000,
      'border_width': 3,
      'button_length': 0,
      'fg_color': gray[1],
      'progress_color': orange[1],
      'button_color': orange[0],
      'button_hover_color': orange[1],
      'text_color': text_color,
      'text_color_disabled': gray[1]
    },
    'CTkSlider': {
      'corner_radius': 1000,
      'button_corner_radius': 1000,
      'border_width': 6,
      'button_length': 0,
      'fg_color': 'gray70',
      'progress_color': gray[0],
      'button_color': orange[0],
      'button_hover_color': orange[1]
    },
    'CTkOptionMenu': {
      'corner_radius': 6,
      'fg_color': orange[0],
      'bg_color': 'transparent',
      'button_color': orange[0],
      'button_hover_color': orange[1],
      'text_color': text_color,
      'text_color_disabled': gray[0]
    },
    'CTkSegmentedButton': {
      'corner_radius': 6,
      'border_width': 0,
      'fg_color': orange[0],
      'selected_color': orange[0],
      'selected_hover_color': orange[1],
      'unselected_color': gray[1],
      'unselected_hover_color': orange[1],
      'text_color': text_color,
      'text_color_disabled': text_color
    },
    'CTkTextbox': {
      'corner_radius': 6,
      'border_width': 0,
      'fg_color': gray[1],
      'border_color': 'transparent',
      'text_color': text_color,
      'scrollbar_button_color': 'gray55',
      'scrollbar_button_hover_color': 'gray40'
    },
    'DropdownMenu': {
      'fg_color': orange[0],
      'hover_color': orange[1],
      'text_color': text_color
    },
    'CTkScrollbar': {
      'corner_radius': 1000,
      'border_spacing': 4,
      'fg_color': 'transparent',
      'button_color': 'gray55',
      'button_hover_color': 'gray40'
    },
    'CTkFont': {
      'macOS': {
        'family': font_macosx,
        'size': 13,
        'weight': 'bold'
      },
      'Windows': {
        'family': font_windows,
        'size': 13,
        'weight': 'bold'
      },
      'Linux': {
        'family': font_linux,
        'size': 13,
        'weight': 'bold'
      }
    }
  }

  with file.open('w') as f:
      json.dump(data, f)