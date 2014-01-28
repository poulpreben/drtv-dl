# Maintainer: Marcus Møller
pkgname=drtv-dl-git
pkgver=20140128
pkgrel=1
pkgdesc="Small command-line program to download videos from DR TV (http://www.dr.dk/tv/)"
arch=(any)
url="https://github.com/marcusmoller/drtv-dle"
license=('public-domain')
depends=(
    'python'
    )
makedepends=('git')

source=("$pkgname"::'git://github.com/marcusmoller/drtv-dl.git')
md5sums=('SKIP')

package() {
    cd "$srcdir/$pkgname"
    install -Dm755 drtv-dl.py ${pkgdir}/usr/bin/drtv-dl
}

