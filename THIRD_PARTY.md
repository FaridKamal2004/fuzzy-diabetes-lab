# Third-party dependencies and data

The Python inference core and browser runtime have no third-party runtime dependencies. The core uses Python's standard library; the site uses system fonts and native SVG.

Test-only dependencies are pinned in `pyproject.toml`: scikit-fuzzy 0.5.0 (BSD-3-Clause), NumPy 2.2.6 (BSD-3-Clause), SciPy 1.15.3 (BSD-3-Clause, plus bundled dependency notices), NetworkX 3.4.2 (BSD-3-Clause), and Matplotlib 3.10.3 (Matplotlib license based on the PSF license). See [scikit-fuzzy](https://github.com/scikit-fuzzy/scikit-fuzzy), [NumPy](https://numpy.org/), [SciPy](https://scipy.org/), [NetworkX](https://networkx.org/), and [Matplotlib](https://matplotlib.org/).

Browser testing uses Playwright 1.58.2 (Apache-2.0) and axe-core Playwright 4.11.1 (MPL-2.0). These packages are not shipped in the static site. Package-manager lockfiles and the test extra specify direct versions; transitive Python test-tool dependencies are resolved by pip.

The original code identifies a Kaggle Pima diabetes benchmark source; see [DATA.md](docs/DATA.md). Raw data and row-level original results are not redistributed. Aggregate benchmark statistics and synthetic fixtures are included. This repository does not grant a license for raw data or assert a blanket license over the original group coursework.
