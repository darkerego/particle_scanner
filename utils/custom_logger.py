import logging
import inspect
import os
import logging
import inspect

class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Get the function name from the record
        func_name = record.funcName

        # Use inspect to get the class name
        class_name = ''
        for frame_info in inspect.stack():
            # Check if the function name matches
            if frame_info.function == func_name:
                args, _, _, value_dict = inspect.getargvalues(frame_info.frame)
                if len(args) and args[0] == 'self':
                    instance = value_dict.get('self', None)
                    if instance:
                        class_name = instance.__class__.__name__ + '.'
                break

        # Check if class and function name are already in the message
        if f"{class_name}{func_name}" not in record.msg:
            record.msg = f"{class_name}{func_name} - {record.msg}"

        return super(CustomFormatter, self).format(record)

# Set up logging as before

def get_logger() -> logging.Logger:
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)
    script_name = os.path.basename(__file__)
    log_file_name = f"{os.path.splitext(script_name)[0]}.log"
    fh = logging.FileHandler(log_file_name)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = CustomFormatter('%(asctime)s  - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    _logger.addHandler(fh)
    _logger.addHandler(ch)
    return _logger




if __name__ == '__main__':
    class MyClass:
        def my_function(self):
            logger.info("This is a log message")
    # Example usage
    logger = get_logger()
    my_instance = MyClass()
    my_instance.my_function()