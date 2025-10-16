# Maintainer: Your Name <your.email@example.com>
pkgname=pass-cli-with-keyboard-total-control
pkgver=1.0.0
pkgrel=1
pkgdesc="AI-generated keyboard-driven GUI for Unix password manager (pass) with total keyboard control"
arch=('any')
url="https://github.com/yourusername/pass-cli-with-keyboard-total-control"
license=('MIT')
depends=(
    'python'
    'python-pyside6'
    'python-qtawesome'
    'pass'
    'gnupg'
)
optdepends=(
    'git: for synchronization with remote repositories'
    'xclip: for clipboard support'
    'wl-clipboard: for clipboard support on Wayland'
)
makedepends=(
    'python-setuptools'
    'python-build'
    'python-installer'
    'python-wheel'
)
source=("${pkgname}-${pkgver}.tar.gz::${url}/archive/v${pkgver}.tar.gz")
sha256sums=('SKIP')  # Заменить на реальный sha256sum после создания релиза

build() {
    cd "${pkgname}-${pkgver}"
    python -m build --wheel --no-isolation
}

package() {
    cd "${pkgname}-${pkgver}"
    python -m installer --destdir="$pkgdir" dist/*.whl
    
    # Install desktop file
    install -Dm644 pass-kb.desktop "$pkgdir/usr/share/applications/pass-kb.desktop"
    
    # Install license
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    
    # Install documentation
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
    install -Dm644 INSTALL.md "$pkgdir/usr/share/doc/$pkgname/INSTALL.md"
}
