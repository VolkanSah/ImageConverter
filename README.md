# WebP Batch Converter (PySide6)

Small tool that can make your life easier\! We all have JPG/PNG to WebP converters, but sometimes you need the reverse. I was so lazy. I gave **Gemini** my old-school script and asked it to build a UI.

## The Workflow Story

Initially, I tried Gradio, but it was *big shit* with all the bugs and overhead.

Then I told Gemini: "Bro, use my basic logic and put it into a clean and stable desktop app using:\*\*

```python
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QFileDialog, QLineEdit, QCheckBox, QLabel, 
    QTabWidget, QMessageBox, QGroupBox, QRadioButton, QSpinBox
)
```

**Grandios\!** The example with Gradio crashed. Google Gemini failed the initial workflow, but after a gentle stroke on the head, I can only say: "Thanks, Gemini, I was so lazy today\!"


## Features

  * **Fast Batch Processing:** Convert hundreds of `.webp` files locally without freezing the UI (thanks to PySide6 threading).
  * **WebP → PNG:** **Lossless** conversion, preserves transparency.
  * **WebP → JPG:** Best quality (`quality=100`, subsampling off). Transparency is converted to white.


###  Credits

Do not forget the :star: this time for **Gemini** and me! 😸
