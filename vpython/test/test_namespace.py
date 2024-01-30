import sys
import vpython

API_NAMES = [
    'Camera',
    'GSversion',
    'GlowWidget',
    'Mouse',
    'RackOutline',
    'ToothOutline',
    'acos',
    'acosh',
    'addpos',
    'adjust_axis',
    'adjust_up',
    'arange',
    'arrow',
    'asin',
    'asinh',
    'atan',
    'atan2',
    'atanh',
    'attach_arrow',
    'attach_light',
    'attach_trail',
    'baseObj',
    'box',
    'bumpmaps',
    'button',
    'canvas',
    'ceil',
    'checkbox',
    'clock',
    'color',
    'combin',
    'comp',
    'compound',
    'cone',
    'controls',
    'convert',
    'copysign',
    'cos',
    'cosh',
    'cross',
    'curve',
    'curveMethods',
    'cylinder',
    'degrees',
    'diff_angle',
    'distant_light',
    'dot',
    'e',
    'ellipsoid',
    'erf',
    'erfc',
    'event_return',
    'exp',
    'expm1',
    'extrusion',
    'fabs',
    'faces',
    'factorial',
    'floor',
    'fmod',
    'frame',
    'frexp',
    'fsum',
    'gamma',
    'gcd',
    'gcurve',
    'gdots',
    'ghbars',
    'gobj',
    'graph',
    'gs_version',
    'gvbars',
    'hat',
    'helix',
    'hypot',
    'inf',
    'isclose',
    'isfinite',
    'isinf',
    'isnan',
    'keysdown',
    'label',
    'ldexp',
    'lgamma',
    'local_light',
    'log',
    'log10',
    'log1p',
    'log2',
    'mag',
    'mag2',
    'menu',
    'meta_canvas',
    'modf',
    'nan',
    'norm',
    'object_rotate',
    'path_object',
    'paths',
    'pi',
    'points',
    'pow',
    'proj',
    'pyramid',
    'quad',
    'radians',
    'radio',
    'random',
    'rate',
    'rate_control',
    'ring',
    'rotate',
    'rotatecp',
    'roundc',
    'scalecp',
    'scene',
    'set_browser',
    'shape_object',
    'shapes',
    'shapespaths',
    'simple_sphere',
    'sin',
    'sinh',
    'sleep',  # From vpython.py
    'slider',
    'sphere',
    'sqrt',
    'standardAttributes',
    'tan',
    'tanh',
    'tau',
    'text',
    'textures',
    'triangle',
    'trunc',
    'vec',
    'vector',
    'version',
    'vertex',
    'winput',
    'wtext',
    'wtext',
    'winput',
    'keysdown',
    'sign'
]


def test_names_in_base_namspace():
    current_names = set(name for name in dir(vpython)
                        if not name.startswith('_'))
    api_name_set = set(API_NAMES)

    python_version = sys.version_info

    # Python 3.7 added remainder to math, so add it to what we
    # expect to see.
    if python_version.major == 3 and python_version.minor >= 7:
        api_name_set.add('remainder')

    # Python 3.8 added even more math functions.
    if python_version.major == 3 and python_version.minor >= 8:
        for name in ['dist', 'comb', 'prod', 'perm', 'isqrt']:
            api_name_set.add(name)

    # Python 3.9 adds three more new math functions.
    if python_version.major == 3 and python_version.minor >= 9:
        for name in ['lcm', 'ulp', 'nextafter']:
            api_name_set.add(name)

    # Python 3.11 adds two more new math functions.
    if python_version.major == 3 and python_version.minor >= 11:
        for name in ['cbrt', 'exp2']:
            api_name_set.add(name)

    # Python 3.12 adds one more new math function.
    if python_version.major == 3 and python_version.minor >= 12:
        for name in ['sumprod']:
            api_name_set.add(name)

    print(sorted(api_name_set - current_names))

    # We may have added new names, so start with this weaker test
    assert api_name_set.issubset(current_names)

    # Ideally this test also passes -- everything in the API is what
    # we should expose and everything we expose is in the API.
    assert api_name_set == current_names
