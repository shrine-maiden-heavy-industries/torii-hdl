# SPDX-License-Identifier: BSD-2-Clause

from typing   import Literal, Optional, Union

from ...build import Attrs, Pins, Resource, Subsignal

__all__ = (
	'ButtonResources',
	'LEDResources',
	'RGBLEDResource',
	'SwitchResources',
)

def _SplitResources(
	*args,
	pins: Union[str, list[str], dict[str, str]], invert: bool = False,
	conn: Optional[Union[tuple[str, int], int]] = None,
	attrs: Optional[Attrs] = None, default_name: str, dir: Literal['i', 'o', 'io']
) -> list[Resource]:

	if not isinstance(pins, (str, list, dict)):
		raise TypeError(f'pins is expected to be a \'str\', \'list\', or \'dict\' not {pins!r}')

	if isinstance(pins, str):
		pins = pins.split()

	if isinstance(pins, list):
		pins = dict(enumerate(pins))

	resources = []

	for number, pin in pins.items():
		ios = [Pins(pin, dir = dir, invert = invert, conn = conn)]
		if attrs is not None:
			ios.append(attrs)
		resources.append(Resource.family(*args, number, default_name = default_name, ios = ios))

	return resources


def LEDResources(*args, **kwargs) -> list[Resource]:
	return _SplitResources(*args, **kwargs, default_name = 'led', dir = 'o')


def RGBLEDResource(
	*args,
	r: str, g: str, b: str, invert: bool = False,
	conn: Optional[Union[tuple[str, int], int]] = None, attrs: Optional[Attrs] = None
) -> Resource:

	ios = []

	ios.append(Subsignal('r', Pins(r, dir = 'o', invert = invert, conn = conn, assert_width = 1)))
	ios.append(Subsignal('g', Pins(g, dir = 'o', invert = invert, conn = conn, assert_width = 1)))
	ios.append(Subsignal('b', Pins(b, dir = 'o', invert = invert, conn = conn, assert_width = 1)))

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(*args, default_name = 'rgb_led', ios = ios)


def ButtonResources(*args, **kwargs) -> list[Resource]:
	return _SplitResources(*args, **kwargs, default_name = 'button', dir = 'i')


def SwitchResources(*args, **kwargs) -> list[Resource]:
	return _SplitResources(*args, **kwargs, default_name = 'switch', dir = 'i')
