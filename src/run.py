from richdisplay.core import Display, LogControl


if __name__ == '__main__':
    log_ctrl = LogControl()

    if not log_ctrl.bail_out:
        display = Display("example_logger")

        display.info("This is an info message.")
        display.debug("This is a debug message.")
        display.error("This is an error message.")
        display.warning("This is a warning message.")
        display.critical("This is a critical message.")

        print("\n")

        display2 = Display("example_logger_2")
        display2.info(
            "This is another info message from a different logger instance.")
        display2.debug(
            "This is another debug message from a different logger instance.")
        display2.error(
            "This is another error message from a different logger instance.")
        display2.warning(
            "This is another warning message from a different logger instance.")
        display2.critical(
            "This is another critical message from a different logger instance.")

        print("\n\n")

    print("tadaaaaa.... The end")
