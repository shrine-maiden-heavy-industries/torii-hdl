# SPDX-License-Identifier: BSD-2-Clause

from os           import devnull, getenv
from pathlib      import Path
from shutil       import copy, make_archive, rmtree

import nox
from nox.sessions import Session

ROOT_DIR  = Path(__file__).parent

BUILD_DIR = ROOT_DIR  / 'build'
CNTRB_DIR = ROOT_DIR  / 'contrib'
DOCS_DIR  = ROOT_DIR  / 'docs'
DIST_DIR  = BUILD_DIR / 'dist'

IN_CI           = getenv('GITHUB_WORKSPACE') is not None
ENABLE_COVERAGE = IN_CI or getenv('TORII_TEST_COVERAGE') is not None
SKIP_EXAMPLES   = getenv('TORII_TEST_NO_EXAMPLES') is not None
SKIP_FORMAL     = getenv('TORII_TEST_NO_FORMAL') is not None

# Default sessions to run
nox.options.sessions = (
	'test',
	'lint',
	'typecheck-mypy'
)

# Try to use `uv`, if not fallback to `virtualenv`
nox.options.default_venv_backend = 'uv|virtualenv'

@nox.session(reuse_venv = True)
def test(session: Session) -> None:
	OUTPUT_DIR = BUILD_DIR / 'tests'
	OUTPUT_DIR.mkdir(parents = True, exist_ok = True)

	BASIC_EXAMPLES  = ROOT_DIR / 'examples' / 'basic'
	FORMAL_EXAMPLES = ROOT_DIR / 'examples' / 'formal'

	unittest_args = ('-m', 'unittest', 'discover', '-s', str(ROOT_DIR))

	session.install('click') # For SBY
	session.install('-e', '.')
	session.install('-e', '.[wasm-sim]')

	if ENABLE_COVERAGE:
		session.log('Coverage support enabled')
		session.install('coverage')
		coverage_args = ('-m', 'coverage', 'run', '-p', f'--rcfile={ROOT_DIR / "pyproject.toml"}',)
		session.env['COVERAGE_CORE'] = 'sysmon'
	else:
		coverage_args = tuple[str]()

	with session.chdir(OUTPUT_DIR):
		session.log('Running core test suite...')
		session.run('python', *coverage_args, *unittest_args, *session.posargs)

		if SKIP_EXAMPLES or len(session.posargs) > 0:
			session.log('Skipping basic examples...')
		else:
			session.log('Testing basic examples...')
			with open(devnull, 'w') as f:
				for example in BASIC_EXAMPLES.iterdir():
					session.run('python', *coverage_args, str(example), 'generate', stdout = f)
					session.run('python', *coverage_args, str(example), 'simulate', stdout = f)

		if SKIP_FORMAL or len(session.posargs) > 0:
			session.log('Skipping formal examples...')
		else:
			session.log('Testing formal examples...')
			for example in FORMAL_EXAMPLES.iterdir():
				session.run('python', *coverage_args, str(example))

		if ENABLE_COVERAGE:
			session.log('Combining Coverage data..')
			session.run('python', '-m', 'coverage', 'combine')

			session.log('Generating XML Coverage report...')
			session.run('python', '-m', 'coverage', 'xml', f'--rcfile={ROOT_DIR / "pyproject.toml"}')

@nox.session(name = 'watch-docs', reuse_venv = True)
def watch_docs(session: Session) -> None:
	OUTPUT_DIR = BUILD_DIR / 'docs'

	session.install('-r', str(DOCS_DIR / 'requirements.txt'))
	session.install('sphinx-autobuild')
	session.install('-e', '.')

	session.run('sphinx-autobuild', str(DOCS_DIR), str(OUTPUT_DIR))

@nox.session(name = 'build-docs', reuse_venv = True)
def build_docs(session: Session) -> None:
	OUTPUT_DIR = BUILD_DIR / 'docs'

	session.install('-r', str(DOCS_DIR / 'requirements.txt'))
	session.install('-e', '.')

	session.run('sphinx-build', '-b', 'html', str(DOCS_DIR), str(OUTPUT_DIR))

@nox.session(name = 'build-docs-multiversion', reuse_venv = True)
def build_docs_multiversion(session: Session) -> None:
	OUTPUT_DIR = BUILD_DIR / 'mv-docs'

	redirect_index = (CNTRB_DIR / 'docs-redirect.html')

	session.install('-r', str(DOCS_DIR / 'requirements.txt'))
	session.install('-e', '.')

	# Workaround for sphinx-contrib/multiversion#58
	# Ask git for the list of tags matching `v*`, and sort them in reverse order by name
	git_tags: str = session.run(
		'git', 'tag', '-l', 'v*', '--sort=-v:refname',
		external = True, silent = True
	) # type: ignore
	# Split the tags and get the first, it *should* be the most recent
	latest = git_tags.splitlines()[0]

	# Build the multi-version docs
	session.run(
		'sphinx-multiversion', '-D', f'smv_latest_version={latest}', str(DOCS_DIR), str(OUTPUT_DIR)
	)

	session.log('Copying docs redirect...')
	# Copy the docs redirect index
	copy(redirect_index, OUTPUT_DIR / 'index.html')

	with session.chdir(OUTPUT_DIR):
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

@nox.session(name = 'build-docset', reuse_venv = True)
def build_docset(session: Session) -> None:
	DOCS_DIR = BUILD_DIR / 'docs'

	# XXX(aki): We can't `session.notify` here because we need the docs first
	build_docs(session)

	session.install('doc2dash')

	# Get the Torii version
	torii_version: str = session.run(
		'python', '-c', 'import torii;print(torii.__version__)',
		silent = True
	)

	with session.chdir(BUILD_DIR):
		# If the docset is already built, shred it because `doc2dash` won't overwrite it
		if (BUILD_DIR / 'Torii.docset').exists():
			rmtree(BUILD_DIR / 'Torii.docset')

		# Build the docset
		session.run(
			'doc2dash', '-n', 'Torii', '-j', '--full-text-search', 'on', str(DOCS_DIR)
		)

		# Compress it
		make_archive(f'torii-{torii_version.strip()}-docset', 'zip', BUILD_DIR, 'Torii.docset')

@nox.session(name = 'dist-docs', reuse_venv = True)
def dist_docs(session: Session) -> None:
	# XXX(aki): We can't `session.notify` here because we need the docs first
	build_docs(session)

	# Get the Torii version
	torii_version: str = session.run(
		'python', '-c', 'import torii;print(torii.__version__)',
		silent = True
	)

	with session.chdir(BUILD_DIR):
		make_archive(f'torii-{torii_version.strip()}-docs', 'zip', BUILD_DIR, 'docs')

@nox.session(name = 'linkcheck-docs', reuse_venv = True)
def linkcheck_docs(session: Session) -> None:
	OUTPUT_DIR = BUILD_DIR / 'docs-linkcheck'

	session.install('-r', str(DOCS_DIR / 'requirements.txt'))
	session.install('-e', '.')

	session.run('sphinx-build', '-b', 'linkcheck', str(DOCS_DIR), str(OUTPUT_DIR))

@nox.session(name = 'typecheck-mypy', reuse_venv = True)
def typecheck_mypy(session: Session) -> None:
	OUTPUT_DIR = BUILD_DIR / 'typing' / 'mypy'
	OUTPUT_DIR.mkdir(parents = True, exist_ok = True)

	session.install('mypy')
	session.install('lxml')
	session.install('types-Pygments', 'types-setuptools')
	session.install('-e', '.')

	session.run(
		'mypy', '--non-interactive', '--install-types', '--pretty',
		'--disallow-any-generics',
		'--cache-dir', str((OUTPUT_DIR / '.mypy-cache').resolve()),
		'-p', 'torii', '--html-report', str(OUTPUT_DIR.resolve())
	)

@nox.session(name = 'typecheck-pyright', reuse_venv = True)
def typecheck_pyright(session: Session) -> None:
	OUTPUT_DIR = BUILD_DIR / 'typing' / 'pyright'
	OUTPUT_DIR.mkdir(parents = True, exist_ok = True)

	session.install('pyright')
	session.install('types-Pygments', 'types-setuptools')
	session.install('-e', '.')

	with (OUTPUT_DIR / 'pyright.log').open('w') as f:
		session.run('pyright', *session.posargs, stdout = f)

@nox.session(reuse_venv = True)
def lint(session: Session) -> None:
	session.install('flake8')
	session.install('ruff')

	session.run(
		'flake8', '--config', str((CNTRB_DIR / '.flake8').resolve()),
		'./torii', './tests', './examples', './docs'
	)
	session.run('ruff', 'check', './torii', './tests', './examples', './docs')

@nox.session(reuse_venv = True)
def dist(session: Session) -> None:
	session.install('build')

	session.run('python', '-m', 'build', '-o', str(DIST_DIR))
