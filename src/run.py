from richdisplay.core import Display, LogControl


if __name__ == '__main__':
    display = Display("richdisplay")

    display.debug("Debug message")
    display.info("Info message")

    display2 = Display("richdisplay2")
    display2.debug("Debug message from display2")
    display2.info("Info message from display2")