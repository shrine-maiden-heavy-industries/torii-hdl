# SPDX-License-Identifier: BSD-2-Clause

from ..._typing   import IODirectionIO
from ...build.dsl import Attrs, Pins, Resource, Subsignal, SubsigArgT, ResourceConn

__all__ = (
	'ButtonResources',
	'LEDResources',
	'RGBLEDResource',
	'SwitchResources',
)

def _SplitResources(
	name_or_number: str | int | None = None, number: int | None = None, *,
	default_name: str, dir: IODirectionIO, pins: str | list[str] | dict[str, str], invert: bool = False,
	conn: ResourceConn | None = None,
	attrs: Attrs | None = None,
) -> list[Resource]:

	if not isinstance(pins, (str, list, dict)):
		raise TypeError(f'pins is expected to be a \'str\', \'list\', or \'dict\' not {pins!r}')

	if isinstance(pins, str):
		pins = pins.split()

	if isinstance(pins, list):
		# NOTE(aki): mypy is /probably/ correct about this one, but
		pins = dict(enumerate(pins)) # type: ignore

	resources: list[Resource] = []

	for idx, pin in pins.items():  # type: ignore
		ios: list[Pins | Attrs] = [ Pins(pin, dir = dir, invert = invert, conn = conn) ]
		if attrs is not None:
			ios.append(attrs)
		# NOTE(aki): This is likely problematic, but
		resources.append(Resource.family(idx, None, default_name = default_name, ios = ios))

	return resources


def LEDResources(
	name_or_number: str | int | None = None, number: int | None = None, *, pins: str | list[str] | dict[str, str],
	invert: bool = False, conn: ResourceConn | None = None, attrs: Attrs | None = None,
) -> list[Resource]:
	return _SplitResources(
		name_or_number, number, default_name = 'led', dir = 'o', pins = pins, invert = invert, conn = conn, attrs = attrs
	)


def RGBLEDResource(
	name_or_number: str | int, number: int | None = None, *,
	r: str, g: str, b: str, invert: bool = False,
	conn: ResourceConn | None = None, attrs: Attrs | None = None
) -> Resource:
	ios: list[SubsigArgT] = []

	ios.append(Subsignal('r', Pins(r, dir = 'o', invert = invert, conn = conn, assert_width = 1)))
	ios.append(Subsignal('g', Pins(g, dir = 'o', invert = invert, conn = conn, assert_width = 1)))
	ios.append(Subsignal('b', Pins(b, dir = 'o', invert = invert, conn = conn, assert_width = 1)))

	if attrs is not None:
		ios.append(attrs)

	return Resource.family(name_or_number, number, default_name = 'rgb_led', ios = ios)


def ButtonResources(
	name_or_number: str | int | None = None, number: int | None = None, *, pins: str | list[str] | dict[str, str],
	invert: bool = False, conn: ResourceConn | None = None, attrs: Attrs | None = None,
) -> list[Resource]:
	return _SplitResources(
		name_or_number, number, default_name = 'button', dir = 'i', pins = pins, invert = invert, conn = conn, attrs = attrs
	)


def SwitchResources(
	name_or_number: str | int | None = None, number: int | None = None, *, pins: str | list[str] | dict[str, str],
	invert: bool = False, conn: ResourceConn | None = None, attrs: Attrs | None = None,
) -> list[Resource]:
	return _SplitResources(
		name_or_number, number, default_name = 'switch', dir = 'i', pins = pins, invert = invert, conn = conn, attrs = attrs
	)
