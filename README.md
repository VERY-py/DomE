# parcl_vc

Небольшой мультиплеерный платформер.
Перед запуском убедится о наличии Pygame, Python 3.12 и выше.

C:\Users\rp13\AppData\Local\Programs\Python\Python313\python.exe D:\CUBE\main.pyw
pygame 2.6.1 (SDL 2.28.4, Python 3.13.3)
Hello from the pygame community. https://www.pygame.org/contribute.html
Traceback (most recent call last):
  File "D:\CUBE\main.pyw", line 8, in <module>
    from system.GUI import GUI
  File "D:\CUBE\system\GUI.py", line 2, in <module>
    import pygame_gui
  File "C:\Users\rp13\AppData\Local\Programs\Python\Python313\Lib\site-packages\pygame_gui\__init__.py", line 8, in <module>
    from pygame_gui.ui_manager import UIManager
  File "C:\Users\rp13\AppData\Local\Programs\Python\Python313\Lib\site-packages\pygame_gui\ui_manager.py", line 9, in <module>
    from pygame_gui.core.interfaces import IUIManagerInterface
  File "C:\Users\rp13\AppData\Local\Programs\Python\Python313\Lib\site-packages\pygame_gui\core\__init__.py", line 1, in <module>
    from pygame_gui.core.ui_appearance_theme import UIAppearanceTheme
  File "C:\Users\rp13\AppData\Local\Programs\Python\Python313\Lib\site-packages\pygame_gui\core\ui_appearance_theme.py", line 12, in <module>
    from pygame_gui.core.interfaces.gui_font_interface import IGUIFontInterface
  File "C:\Users\rp13\AppData\Local\Programs\Python\Python313\Lib\site-packages\pygame_gui\core\interfaces\__init__.py", line 4, in <module>
    from pygame_gui.core.interfaces.font_dictionary_interface import (
        IUIFontDictionaryInterface,
    )
  File "C:\Users\rp13\AppData\Local\Programs\Python\Python313\Lib\site-packages\pygame_gui\core\interfaces\font_dictionary_interface.py", line 3, in <module>
    from pygame import DIRECTION_LTR
ImportError: cannot import name 'DIRECTION_LTR' from 'pygame' (C:\Users\rp13\AppData\Local\Programs\Python\Python313\Lib\site-packages\pygame\__init__.py)

Process finished with exit code 1
