import sys

from jupyter_client import kernelspec


# If we get this far, vpnotebook ought to have been installed and
# we should have a vpython kernel.

assert 'vpython' in kernelspec.find_kernel_specs().keys()

# Python 2.7 and 3.4:
major, minor = sys.version_info[0:2]
if major == 2 or (major == 3 and minor == 4):
    # Make sure vpython is installed. The import is expected to fail because it
    # tries to connect to a jupyter comm, and we are not running a notebook.
    # The test is really that the error message expected if that is the
    # failure is the actual error message.
    try:
        import vpython
    except Exception as e:
        assert "The non-notebook version of vpython requires" in str(e)
    except OSError as e:
        if sys.platform.startswith('win'):
            assert "The system cannot find the path specified" in str(e)
        else:
            assert "No such file or directory" in str(e)
