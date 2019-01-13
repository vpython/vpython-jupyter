import os

travis_tag = os.getenv('TRAVIS_TAG')
appveyor_tag = os.getenv('APPVEYOR_REPO_TAG_NAME')


def generate_label(version):
    dev_names = ['dev', 'alpha', 'beta', 'rc']

    is_dev = any(name in version for name in dev_names)

    # Output is the name of the label to which the package should be
    # uploaded on anaconda.org
    if is_dev:
        print('pre-release')
    else:
        print('main')


if travis_tag:
    generate_label(travis_tag)
elif appveyor_tag:
    generate_label(appveyor_tag)
else:
    print('main')
