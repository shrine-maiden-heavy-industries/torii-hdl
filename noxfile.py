# SPDX-License-Identifier: BSD-3-Clause


from os             import link, getenv
from pathlib        import Path
from setuptools_scm import get_version, ScmVersion
from shutil         import copy

import nox
from nox.sessions   import Session

ROOT_DIR  = Path(__file__).parent

BUILD_DIR = (ROOT_DIR  / 'build')
CNTRB_DIR = (ROOT_DIR  / 'contrib')
DOCS_DIR  = (ROOT_DIR  / 'docs')
DIST_DIR  = (BUILD_DIR / 'dist')

IN_CI           = getenv('GITHUB_WORKSPACE') is not None
ENABLE_COVERAGE = IN_CI or getenv('TORII_TEST_COVERAGE') is not None
ENABLE_FORMAL   = getenv('TORII_TEST_FORMAL') is not None

# Default sessions to run
nox.options.sessions = (
	'test',
	'lint',
	'typecheck'
)

def torii_version() -> str:
	def scheme(version: ScmVersion) -> str:
		if version.tag and not version.distance:
			return version.format_with('')
		else:
			return version.format_choice('+{node}', '+{node}.dirty')

	return get_version(
		root           = str(ROOT_DIR),
		version_scheme = 'guess-next-dev',
		local_scheme   = scheme,
		relative_to    = __file__
	)

@nox.session(reuse_venv = True)
def test(session: Session) -> None:
	out_dir = (BUILD_DIR / 'tests')
	out_dir.mkdir(parents = True, exist_ok = True)

	unitest_args = ('-m', 'unittest', 'discover', '-s', str(ROOT_DIR))

	session.install('click') # For SBY
	session.install('.')

	if ENABLE_COVERAGE:
		session.log('Coverage support enabled')
		session.install('coverage')
		coverage_args = (
			'-m', 'coverage', 'run',
			f'--rcfile={CNTRB_DIR / "coveragerc"}'
		)
	else:
		coverage_args = ()

	session.chdir(str(out_dir))

	if ENABLE_FORMAL:
		FORMAL_EXAMPLES = ROOT_DIR / 'examples' / 'formal'
		session.log('Running formal tests')
		for example in FORMAL_EXAMPLES.iterdir():
			session.run(
				'python', *coverage_args, str(example)
			)
	else:
		session.log('Running standard test suite')
		session.run(
			'python', *coverage_args, *unitest_args, *session.posargs
		)

	if ENABLE_COVERAGE:
		session.run(
			'python', '-m', 'coverage', 'xml',
			f'--rcfile={CNTRB_DIR / "coveragerc"}'
		)

@nox.session(name = 'build-docs')
def build_docs(session: Session) -> None:
	out_dir = (BUILD_DIR / 'docs')
	session.install('-r', str(DOCS_DIR / 'requirements.txt'))
	session.install('.')
	session.run('sphinx-build', '-b', 'html', str(DOCS_DIR), str(out_dir))

@nox.session(name = 'build-docs-multiversion')
def build_docs_multiversion(session: Session) -> None:
	out_dir = (BUILD_DIR / 'mv-docs')

	redirect_index = (CNTRB_DIR / 'docs-redirect.html')

	session.install('-r', str(DOCS_DIR / 'requirements.txt'))
	session.install('.')

	# Workaround for sphinx-contrib/multiversion#58
	# Ask git for the list of tags matching `v*`, and sort them in reverse order by name
	git_tags: str = session.run(
		'git', 'tag', '-l', 'v*', '--sort=-v:refname',
		external=True, silent=True
	) # type: ignore
	# Split the tags and get the first, it *should* be the most recent
	latest = git_tags.splitlines()[0]

	# Build the multi-version docs
	session.run(
		'sphinx-multiversion', '-D', f'smv_latest_version={latest}', str(DOCS_DIR), str(out_dir)
	)

	session.log('Copying docs redirect...')
	# Copy the docs redirect index
	copy(redirect_index, out_dir / 'index.html')

	with session.chdir(out_dir):
		latest_link = Path('latest')
		docs_dev    = Path('main')
		docs_tag    = Path(latest)

		session.log('Copying needed GitHub pages files...')

		copy(docs_dev / 'CNAME', 'CNAME')
		copy(docs_dev / '.nojekyll', '.nojekyll')

		session.log('Creating symlink to latest docs...')
		# If the symlink exists, unlink it
		if latest_link.exists():
			latest_link.unlink()

		# Check to make sure the latest tag has some docs
		if docs_tag.exists():
			# Create a symlink from `/latest` to the latest tag
			latest_link.symlink_to(docs_tag)
		else:
			session.warn(f'Docs for {latest} did not seem to be built, using development docs instead')
			# Otherwise, link to `main`
			latest_link.symlink_to(docs_dev)

@nox.session(name = 'linkcheck-docs')
def linkcheck_docs(session: Session) -> None:
	out_dir = (BUILD_DIR / 'docs-linkcheck')
	session.install('-r', str(DOCS_DIR / 'requirements.txt'))
	session.install('.')
	session.run('sphinx-build', '-b', 'linkcheck', str(DOCS_DIR), str(out_dir))

@nox.session(name = 'typecheck-mypy')
def typecheck_mypy(session: Session) -> None:
	out_dir = (BUILD_DIR / 'typing' / 'mypy')
	out_dir.mkdir(parents = True, exist_ok = True)

	session.install('mypy')
	session.install('lxml')
	session.install('.')
	session.run(
		'mypy', '--non-interactive', '--install-types', '--pretty',
		'--disallow-any-generics',
		'--cache-dir', str((out_dir / '.mypy-cache').resolve()),
		'--config-file', str((CNTRB_DIR / '.mypy.ini').resolve()),
		'-p', 'torii', '--html-report', str(out_dir.resolve())
	)

@nox.session(name = 'typecheck-pyright')
def typecheck_pyright(session: Session) -> None:
	out_dir = (BUILD_DIR / 'typing' / 'pyright')
	out_dir.mkdir(parents = True, exist_ok = True)

	session.install('pyright')
	session.install('.')

	with (out_dir / 'pyright.log').open('w') as f:
		session.run(
			'pyright', '-p', str((CNTRB_DIR / 'pyrightconfig.json').resolve()), *session.posargs,
			stdout = f
		)

@nox.session
def lint(session: Session) -> None:
	session.install('flake8')

	session.run(
		'flake8', '--config', str((CNTRB_DIR / '.flake8').resolve()),
		'./torii', './tests', './examples', './docs'
	)

@nox.session
def dist(session: Session) -> None:
	session.install('build')
	session.run(
		'python', '-m', 'build',
		'-o', str(DIST_DIR)
	)

@nox.session
def upload(session: Session) -> None:
	session.install('twine')
	dist(session)
	session.log(f'Uploading torii-{torii_version()} to PyPi')
	session.run(
		'python', '-m', 'twine',
		'upload', f'{DIST_DIR}/torii-{torii_version()}*'
	)
