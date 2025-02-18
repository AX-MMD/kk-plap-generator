import traceback

from kk_plap_generator.gui import PlapUI

# Run PlapUI

if __name__ == "__main__":
    try:
        PlapUI.run()
    except Exception:
        traceback.print_exc()
