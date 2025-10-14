# SPDX-License-Identifier: BSD-2-Clause

from ..._typing   import IODirectionIO
from ...build.dsl import Attrs, Pins, Resource, ResourceConn, SubsigArgT, Subsignal

__all__ = (
	'ButtonResources',
	'LEDResources',
	'RGBLEDResource',
	'SwitchResources',
)

def _SplitResources(
	name_or_number: str | int | None = None, number: int | None = None, *, default_name: str, dir: IODirectionIO,
	pins: str | list[str] | dict[int, str], invert: bool = False, conn: ResourceConn | None = None,
	attrs: Attrs | None = None,
) -> list[Resource]:
	'''
	Create an array of simple named resources from a collection of pins.

	Warning
	-------
	This is a Torii-internal API for splitting resources, if you are looking to split LEDs, Buttons,
	or Switches, please use the appropriate resource methods for those, as their API is stable while
	this API is **not**.

	Parameters
	----------
	name_or_number: str | int | None
		The common name for the split resources, or the explicit start index for the
		resources.

		If the name is not supplied the value in ``default_name`` will be used.

	number: int | None
		The explicit start index if ``name_or_number`` is the name of the resources.

	default_name: str
		The name all the resources will be under, for example `led`.

	dir: IODirecitionIO
		IO Direction for the resource pin.

	pins: str | list[str] | dict[int, str]
		The collection of pints to split into individual resources.

	invert: bool
		Invert the logic on the pin for the resource.

	offset: int | None
		The index offset to start resource splitting at.

		This allows you to use multiple split resources in the same resource collection. This is useful
		for things like ensure all LEDs have the same resource name, but can be split over IO bank voltages
		or connectors.

	conn: ResourceConn | None
		The connector to use for the split resources if applicable.

	attrs: Attrs | None
		The attributes to apply to the split resources if applicable.
	'''

	if not isinstance(pins, (str, list, dict)):
		raise TypeError(f'pins is expected to be a \'str\', \'list\', or \'dict\' not {pins!r}')

	if isinstance(pins, str):
		pins = pins.split()

	if isinstance(pins, list):
		# NOTE(aki): mypy is /probably/ correct about this one, but
		pins = dict(enumerate(pins)) # type: ignore

	resources: list[Resource] = []

	name: str | None = None
	if isinstance(name_or_number, str):
		name = name_or_number

	if isinstance(name_or_number, int):
		number = name_or_number

	if number is None:
		number = 0

	for idx, pin in pins.items():  # type: ignore
		ios: list[Pins | Attrs] = [ Pins(pin, dir = dir, invert = invert, conn = conn) ]
		if attrs is not None:
			ios.append(attrs)
		# NOTE(aki): This is likely problematic, but
		res_index = idx + number
		resources.append(Resource.family(
			res_index if name is None else name,
			res_index if name is not None else None,
			default_name = default_name, ios = ios
		))

	return resources

def ButtonResources(
	name_or_number: str | int | None = None, number: int | None = None, *,
	pins: str | list[str] | dict[int, str], invert: bool = False,
	conn: ResourceConn | None = None, attrs: Attrs | None = None,
) -> list[Resource]:
	'''
	Turn a list of pins connected to switches into individual button resources.

	Parameters
	----------
	name_or_number: str | int | None
		The common name for the button resources, or the explicit start index for the
		resources.

		If the name is not supplied, the resources will all have the common name of ``button``.

	number: int | None
		The explicit start index if ``name_or_number`` is the name of the button resources.

	pins: str | list[str] | dict[int, str]
		The pins for each button.

	invert: bool
		Invert the logic for the buttons.

	conn: ResourceConn | None
		The connector these buttons are on if applicable.

	attrs: Attrs | None
		The attributes to apply to the buttons if applicable.

	Returns
	-------
	list[Resource]
		The collection of expanded button resources.
	'''

	return _SplitResources(
		name_or_number, number, default_name = 'button', dir = 'i', pins = pins, invert = invert,
		conn = conn, attrs = attrs
	)

def LEDResources(
	name_or_number: str | int | None = None, number: int | None = None, *,
	pins: str | list[str] | dict[int, str], invert: bool = False,
	conn: ResourceConn | None = None, attrs: Attrs | None = None,
) -> list[Resource]:
	'''
	Turn a list of pins connected to switches into individual LED resources.

	Parameters
	----------
	name_or_number: str | int | None
		The common name for the LED resources, or the explicit start index for the
		resources.

		If the name is not supplied, the resources will all have the common name of ``led``.

	number: int | None
		The explicit start index if ``name_or_number`` is the name of the LED resources.

	pins: str | list[str] | dict[int, str]
		The pins for each LED.

	invert: bool
		Invert the logic for the LEDs.

	conn: ResourceConn | None
		The connector these LEDs are on if applicable.

	attrs: Attrs | None
		The attributes to apply to the LEDs if applicable.

	Returns
	-------
	list[Resource]
		The collection of expanded LED resources.
	'''

	return _SplitResources(
		name_or_number, number, default_name = 'led', dir = 'o', pins = pins, invert = invert,
		conn = conn, attrs = attrs
	)

def RGBLEDResource(
	name_or_number: str | int, number: int | None = None, *,
	r: str, g: str, b: str, invert: bool = False,
	conn: ResourceConn | None = None, attrs: Attrs | None = None
) -> Resource:
	'''
	Create an RGB LED resource.

	This can be either common cathode or common anode, you simply need to set ``invert`` as
	appropriate.

	Parameters
	----------
	name_or_number: str | int | None
		The name of this resource, or the explicit number to assign this resource.

		If no name is specified the default resource name of ``rgb_led`` is used.

	number: int | None
		The explicit number to assign this resource.

	r: str
		The LEDs red channel.

	g: str
		The LEDs green channel.

	b: str
		The LEDs blue channel.

	invert: bool
		Invert the logic for the buttons.

	conn: ResourceConn | None
		The connector these buttons are on if applicable.

	attrs: Attrs | None
		The attributes to apply to the buttons if applicable.

	Returns
	-------
	Resource
		The newly constructed RGB LED resource.
	'''

	ios: list[SubsigArgT] = []

	ios.append(Subsignal('r', Pins(r, dir = 'o', invert = invert, conn = conn, assert_width = 1)))
	ios.append(Subsignal('g', Pins(g, dir = 'o', invert = invert, conn = conn, assert_width = 1)))
	ios.append(Subsignal('b', Pins(b, dir = 'o', invert = invert, conn = conn, assert_width = 1)))

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'rgb_led', ios = ios)

def SwitchResources(
	name_or_number: str | int | None = None, number: int | None = None, *,
	pins: str | list[str] | dict[int, str], invert: bool = False,
	conn: ResourceConn | None = None, attrs: Attrs | None = None,
) -> list[Resource]:
	'''
	Turn a list of pins connected to switches into individual switch resources.

	Parameters
	----------
	name_or_number: str | int | None
		The common name for the switch resources, or the explicit start index for the
		resources.

		If the name is not supplied, the resources will all have the common name of ``switch``.

	number: int | None
		The explicit start index if ``name_or_number`` is the name of the switch resources.

	pins: str | list[str] | dict[int, str]
		The pins for each switch.

	invert: bool
		Invert the logic for the switches.

	conn: ResourceConn | None
		The connector these switches are on if applicable.

	attrs: Attrs | None
		The attributes to apply to the switches if applicable.

	Returns
	-------
	list[Resource]
		The collection of expanded switch resources.
	'''

	return _SplitResources(
		name_or_number, number, default_name = 'switch', dir = 'i', pins = pins, invert = invert,
		conn = conn, attrs = attrs
	)
